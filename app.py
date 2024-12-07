from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from flask_wtf.csrf import CSRFProtect
import random
from functools import wraps
from flask import abort
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///homework.db'
app.config['WTF_CSRF_CHECK_DEFAULT'] = False
csrf = CSRFProtect(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 配置上传文件的存储路径
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'  # 设置默认语言为简体中文

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_ungrouped = db.Column(db.Boolean, default=False)  # 标记是否为未分组
    members = db.relationship('GroupMember', backref='group', lazy=True)

class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.Boolean, default=False)  # False: 未完成, True: 已完成
    user = db.relationship('User', backref='group_memberships')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# 添加自定义过滤器
@app.template_filter('count_members')
def count_members(groups):
    return sum(len(group.members) for group in groups if not group.is_ungrouped)

@app.template_filter('count_completed')
def count_completed(groups):
    return sum(sum(1 for member in group.members if member.status) 
              for group in groups if not group.is_ungrouped)

# Routes
@app.route('/')
def index():
    tasks = Task.query.order_by(Task.created_at.desc()).first()
    # 只获取非未分组的组
    groups = Group.query.filter_by(is_ungrouped=False).all()
    return render_template('index.html', tasks=tasks, groups=groups)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin_dashboard' if user.is_admin else 'index'))
        flash('用户名或密码错误')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    # 获取所有作业并计算完成情况
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    for task in tasks:
        # 计算作业完成情况
        total_members = GroupMember.query.count()
        completed_members = GroupMember.query.filter_by(status=True).count()
        task.total_count = total_members
        task.completed_count = completed_members

    groups = Group.query.all()
    # 确保有一个未分组的组
    ungrouped = Group.query.filter_by(is_ungrouped=True).first()
    if not ungrouped:
        ungrouped = Group(name="未分组", is_ungrouped=True)
        db.session.add(ungrouped)
        db.session.commit()
        groups = Group.query.all()  # 重新查询以包含新创建的组
    return render_template('admin.html', groups=groups, ungrouped=ungrouped, tasks=tasks)

@app.route('/api/tasks', methods=['POST'])
@login_required
@admin_required
def create_task():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        title = data.get('title')
        content = data.get('content')
        deadline = data.get('deadline')
        
        if not title or not content:
            return jsonify({'error': '标题和内容不能为空'}), 400
            
        task = Task(
            title=title,
            content=content,
            deadline=datetime.strptime(deadline, '%Y-%m-%dT%H:%M') if deadline else None
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'message': '作业发布成功',
            'task': {
                'id': task.id,
                'title': task.title,
                'content': task.content,
                'deadline': task.deadline.strftime('%Y-%m-%d %H:%M') if task.deadline else None
            }
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'创建作业失败: {str(e)}')
        return jsonify({'error': '创建作业失败，请重试'}), 500

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
@admin_required
def update_task(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        task.title = data.get('title', task.title)
        task.content = data.get('content', task.content)
        task.deadline = datetime.strptime(data['deadline'], '%Y-%m-%dT%H:%M') if data.get('deadline') else None
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '作业更新成功'
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'更新作业失败: {str(e)}')
        return jsonify({'error': '更新作业失败，请重试'}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_task(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '作业删除成功'
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'删除作业失败: {str(e)}')
        return jsonify({'error': '删除作业失败，请重试'}), 500

@app.route('/api/groups', methods=['POST', 'PUT'])
@login_required
def manage_group():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        data = request.get_json()
        if not data or not data.get('name'):
            return jsonify({'error': 'Missing group name'}), 400

        if request.method == 'POST':
            group = Group(name=data['name'])
            db.session.add(group)
            db.session.commit()
            return jsonify({'id': group.id, 'message': 'Group created successfully'})
        else:  # PUT
            if not data.get('id'):
                return jsonify({'error': 'Missing group ID'}), 400
            
            group = Group.query.get_or_404(data['id'])
            group.name = data['name']
            db.session.commit()
            return jsonify({'message': 'Group updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups/<int:group_id>', methods=['DELETE'])
@login_required
def delete_group(group_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        group = Group.query.get_or_404(group_id)
        # 删除组内所有成员
        GroupMember.query.filter_by(group_id=group_id).delete()
        db.session.delete(group)
        db.session.commit()
        return jsonify({'message': 'Group deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups/reset', methods=['POST'])
@login_required
def reset_groups():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # 删除所有成员和小组
        GroupMember.query.delete()
        Group.query.delete()
        db.session.commit()
        return jsonify({'message': 'All groups have been reset'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@csrf.exempt
@app.route('/api/members', methods=['POST'])
@login_required
@admin_required
def add_member():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的请求数据'}), 400
            
        group_id = data.get('group_id')
        username = data.get('username')
        
        if not group_id or not username:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
            
        # 检查组是否存在
        group = Group.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': '小组不存在'}), 404
            
        # 检查是否已达到组员上限
        current_members = GroupMember.query.filter_by(group_id=group_id).count()
        if not group.is_ungrouped and current_members >= 5:
            return jsonify({'success': False, 'error': '小组已满(最多5人)'}), 400
            
        # 检查组内是否已存在同名用户
        existing_members = GroupMember.query.join(User).filter(
            GroupMember.group_id == group_id,
            User.username == username
        ).first()
        if existing_members:
            return jsonify({'success': False, 'error': '该小组中已存在同名成员'}), 400

        # 检查用户是否已存在于任何组
        user = User.query.filter_by(username=username).first()
        if user:
            existing_member = GroupMember.query.filter_by(user_id=user.id).first()
            if existing_member:
                return jsonify({'success': False, 'error': '该用户已在其他组中'}), 400
        else:
            # 创建新用户
            user = User(
                username=username,
                password_hash=generate_password_hash(username),
                is_admin=False
            )
            db.session.add(user)
            
        try:
            # 创建组员关系
            member = GroupMember(user_id=user.id, group_id=group_id)
            db.session.add(member)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'member': {
                    'id': member.id,
                    'username': user.username,
                    'status': member.status
                }
            })
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Failed to add member: {str(e)}')
            return jsonify({'success': False, 'error': '添加成员失败'}), 500
            
    except Exception as e:
        app.logger.error(f'Request processing failed: {str(e)}')
        return jsonify({'success': False, 'error': '服务器内部错误'}), 500

@app.route('/api/members/move', methods=['POST'])
@login_required
@admin_required
def move_member():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        member_id = data.get('member_id')
        target_group_id = data.get('target_group_id')
        
        if not member_id or not target_group_id:
            return jsonify({'error': '缺少必要参数'}), 400
        
        member = GroupMember.query.get(member_id)
        if not member:
            return jsonify({'error': '成员不存在'}), 404
            
        target_group = Group.query.get(target_group_id)
        if not target_group:
            return jsonify({'error': '目标组不存在'}), 404
            
        # 如果不是移动到未分组，检查目标组人数
        if not target_group.is_ungrouped:
            current_members = GroupMember.query.filter_by(group_id=target_group_id).count()
            if current_members >= 5:
                return jsonify({'error': '目标组已满(最多5人)'}), 400
        
        # 更新成员所属组
        old_group_id = member.group_id
        member.group_id = target_group_id
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '成员移动成功',
            'member': {
                'id': member.id,
                'username': member.user.username,
                'status': member.status
            },
            'old_group_id': old_group_id,
            'new_group_id': target_group_id
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'移动成员失败: {str(e)}')
        return jsonify({'error': '移动成员失败，请重试'}), 500

@csrf.exempt
@app.route('/api/members/status', methods=['POST'])
@login_required
def toggle_member_status():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的请求数据'}), 400
            
        member_id = data.get('member_id')
        status = data.get('status')
        
        app.logger.info(f'Received status update request: member_id={member_id}, status={status}')
        
        # 验证member_id
        if not member_id:
            return jsonify({'success': False, 'error': '缺少成员ID'}), 400
            
        try:
            member_id = int(member_id)
            if member_id <= 0:
                return jsonify({'success': False, 'error': '无效的成员ID'}), 400
        except (TypeError, ValueError):
            app.logger.error(f'Invalid member_id format: {member_id}')
            return jsonify({'success': False, 'error': '无效的成员ID格式'}), 400
            
        # 验证status
        if status is None:
            return jsonify({'success': False, 'error': '缺少状态参数'}), 400
            
        # 查询成员
        member = GroupMember.query.get(member_id)
        if not member:
            app.logger.error(f'Member not found: id={member_id}')
            return jsonify({'success': False, 'error': '成员不存在'}), 404
            
        # 更新状态
        try:
            old_status = member.status
            member.status = bool(status)
            db.session.commit()
            
            app.logger.info(f'Status updated: member_id={member_id}, old_status={old_status}, new_status={member.status}')
            
            return jsonify({
                'success': True,
                'message': '状态更新成功',
                'member_id': member_id,
                'old_status': old_status,
                'new_status': member.status
            })
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Failed to update status: {str(e)}')
            return jsonify({'success': False, 'error': '更新状态失败'}), 500
            
    except Exception as e:
        app.logger.error(f'Request processing failed: {str(e)}')
        return jsonify({'success': False, 'error': '服务器内部错误'}), 500

@csrf.exempt
@app.route('/api/members/import', methods=['POST'])
@login_required
@admin_required
def import_members():
    try:
        data = request.get_json()
        if not data or 'members' not in data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        members = data.get('members', [])
        if not members:
            return jsonify({'error': '成员列表为空'}), 400
            
        errors = []
        success_count = 0
        
        # 获取或创建未分组组
        ungrouped = Group.query.filter_by(is_ungrouped=True).first()
        if not ungrouped:
            ungrouped = Group(name='未分组', is_ungrouped=True)
            db.session.add(ungrouped)
            db.session.commit()
        
        for member_name in members:
            member_name = member_name.strip()
            if not member_name:
                continue
                
            try:
                # 检查用户是否已存在
                user = User.query.filter_by(username=member_name).first()
                if user:
                    # 检查用户是否已在某个组
                    existing_member = GroupMember.query.filter_by(user_id=user.id).first()
                    if existing_member:
                        errors.append(f'用户 {member_name} 已在其他组中')
                        continue
                else:
                    # 创建新用户，使用用户名作为密码
                    user = User(
                        username=member_name,
                        password_hash=generate_password_hash(member_name)
                    )
                    db.session.add(user)
                    db.session.flush()  # 获取新用户的ID
                
                # 添加到未分组
                member = GroupMember(user_id=user.id, group_id=ungrouped.id)
                db.session.add(member)
                success_count += 1
                
            except Exception as e:
                errors.append(f'导入用户 {member_name} 失败: {str(e)}')
                continue
        
        db.session.commit()
        
        message = f'成功导入 {success_count} 名成员'
        if errors:
            message += f'，但有 {len(errors)} 个错误'
            
        return jsonify({
            'success': True,
            'message': message,
            'errors': errors,
            'success_count': success_count
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'批量导入失败: {str(e)}')
        return jsonify({
            'error': '批量导入失败，请重试',
            'details': str(e)
        }), 500

@app.route('/api/members/auto-group', methods=['POST'])
@login_required
def auto_group_members():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    members_per_group = data.get('members_per_group', 5)
    
    try:
        # 获取未分组的成员
        ungrouped = Group.query.filter_by(is_ungrouped=True).first()
        if not ungrouped:
            return jsonify({'error': '没有未分组的成员'}), 400
            
        members = GroupMember.query.filter_by(group_id=ungrouped.id).all()
        if not members:
            return jsonify({'error': '没有未分组的成员'}), 400
        
        # 随机打乱成员顺序
        import random
        random.shuffle(members)
        
        # 计算需要创建的组数
        total_members = len(members)
        num_groups = (total_members + members_per_group - 1) // members_per_group
        
        # 确保每组至少有2人(如果可能的话)
        if num_groups > 1 and total_members / num_groups < 2:
            num_groups = total_members // 2
        
        # 计算基本每组人数和余数
        base_members = total_members // num_groups
        extra_members = total_members % num_groups
        
        # 创建新组
        new_groups = []
        existing_names = set(g.name for g in Group.query.filter_by(is_ungrouped=False).all())
        
        for i in range(num_groups):
            # 生成不重复的组名
            group_number = i + 1
            group_name = f'Group {group_number}'
            while group_name in existing_names:
                group_number += 1
                group_name = f'Group {group_number}'
            
            group = Group(name=group_name)
            db.session.add(group)
            db.session.commit()
            new_groups.append(group)
            existing_names.add(group_name)
        
        # 分配成员到组
        member_index = 0
        for i, group in enumerate(new_groups):
            # 计算当前组应该分配的成员数
            current_group_size = base_members + (1 if i < extra_members else 0)
            
            # 分配成员
            for _ in range(current_group_size):
                if member_index < len(members):
                    members[member_index].group_id = group.id
                    member_index += 1
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'成功创建{num_groups}个小组',
            'groups': [{
                'id': g.id,
                'name': g.name,
                'member_count': len([m for m in members if m.group_id == g.id])
            } for g in new_groups]
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'自动分组失败: {str(e)}')
        return jsonify({'error': f'自动分组失败: {str(e)}'}), 500

@app.route('/admin/change-password', methods=['GET', 'POST'])
@login_required
@admin_required
def change_password():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': '无效的请求数据'}), 400
                
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
            
            if not all([current_password, new_password, confirm_password]):
                return jsonify({'error': '请填写所有必填字段'}), 400
                
            if new_password != confirm_password:
                return jsonify({'error': '两次输入的新密码不一致'}), 400
                
            if not check_password_hash(current_user.password_hash, current_password):
                return jsonify({'error': '当前密码错误'}), 400
                
            if len(new_password) < 6:
                return jsonify({'error': '新密码长度不能少于6个字符'}), 400
                
            current_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '密码修改成功'
            })
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'修改密码失败: {str(e)}')
            return jsonify({'error': '修改密码失败，请重试'}), 500
    
    return render_template('change_password.html')

@app.route('/upload/image', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def upload_image():
    try:
        if 'upload' not in request.files:
            return """
                <script>
                    window.parent.CKEDITOR.tools.callFunction({}, '', '没有文件被上传');
                </script>
            """.format(request.args.get('CKEditorFuncNum'))
            
        file = request.files['upload']
        if file.filename == '':
            return """
                <script>
                    window.parent.CKEDITOR.tools.callFunction({}, '', '没有选择文件');
                </script>
            """.format(request.args.get('CKEditorFuncNum'))
            
        if file and allowed_file(file.filename):
            # 确保文件名安全
            filename = secure_filename(file.filename)
            # 添加时间戳避免文件名冲突
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            
            # 确保上传目录存在
            upload_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_path, exist_ok=True)
            
            # 保存文件
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
            
            # 返回CKEditor所需的响应格式
            url = url_for('static', filename=f'uploads/{filename}', _external=True)
            return """
                <script>
                    window.parent.CKEDITOR.tools.callFunction({}, '{}');
                </script>
            """.format(request.args.get('CKEditorFuncNum'), url)
        else:
            return """
                <script>
                    window.parent.CKEDITOR.tools.callFunction({}, '', '不支持的文件类型');
                </script>
            """.format(request.args.get('CKEditorFuncNum'))
    except Exception as e:
        app.logger.error(f'上传图片失败: {str(e)}')
        return """
            <script>
                window.parent.CKEDITOR.tools.callFunction({}, '', '上传失败，请重试');
            </script>
        """.format(request.args.get('CKEditorFuncNum'))

@app.route('/api/members/delete', methods=['POST'])
@login_required
@admin_required
def delete_member():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求���据'}), 400
            
        member_id = data.get('member_id')
        if not member_id:
            return jsonify({'error': '缺少成员ID'}), 400
            
        member = GroupMember.query.get(member_id)
        if not member:
            return jsonify({'error': '成员不存在'}), 404
            
        db.session.delete(member)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '成员删除成功'
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'删除成员失败: {str(e)}')
        return jsonify({'error': '删除成员失败，请重试'}), 500

def init_db():
    with app.app_context():
        # 创建所有表（如果不存在）
        db.create_all()
        
        # 检查是否需要创建管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin'),
                is_admin=True
            )
            db.session.add(admin)
            print('创建管理员用户成功')
        
        # 检查是否需要创建分组
        if not Group.query.first():
            # 创建未分组
            ungrouped = Group(name='未分组', is_ungrouped=True)
            db.session.add(ungrouped)
            
            # 创建12个默认分组
            for i in range(1, 13):
                group = Group(name=f'第{i}组', is_ungrouped=False)
                db.session.add(group)
            
            try:
                db.session.commit()
                print('创建默认分组成功')
            except Exception as e:
                db.session.rollback()
                print(f'创建默认分组失败：{str(e)}')
                return
        
        try:
            db.session.commit()
            print('数据库初始化完成')
            print('默认管理员账号：admin')
            print('默认管理员密码：admin')
        except Exception as e:
            db.session.rollback()
            print(f'数据库初始化失败：{str(e)}')

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(host='0.0.0.0', port=5678, debug=True)
