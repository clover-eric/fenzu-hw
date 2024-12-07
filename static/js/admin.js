document.addEventListener('DOMContentLoaded', function() {
    // Task form submission
    const taskForm = document.getElementById('taskForm');
    taskForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const taskData = {
            title: document.getElementById('title').value,
            content: document.getElementById('content').value,
            deadline: document.getElementById('deadline').value || null
        };

        fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                location.reload();
            }
        });
    });

    // Reset groups button
    document.getElementById('resetGroups').addEventListener('click', function() {
        if (confirm('确定要重置所有分组吗？这将清除所有现有的分组信息。')) {
            fetch('/api/groups/reset', {
                method: 'POST'
            })
            .then(() => location.reload());
        }
    });

    // Export data button
    document.getElementById('exportData').addEventListener('click', function() {
        window.location.href = '/api/export';
    });

    // Edit group button
    document.querySelectorAll('.edit-group').forEach(btn => {
        btn.addEventListener('click', function() {
            const groupId = this.dataset.groupId;
            // Implement edit group modal/functionality
        });
    });

    // Delete group button
    document.querySelectorAll('.delete-group').forEach(btn => {
        btn.addEventListener('click', function() {
            const groupId = this.dataset.groupId;
            if (confirm('确定要删除这个小组吗？')) {
                fetch(`/api/groups/${groupId}`, {
                    method: 'DELETE'
                })
                .then(() => location.reload());
            }
        });
    });

    // 初始化 TinyMCE
    tinymce.init({
        selector: '#content',
        plugins: 'lists link image table code',
        toolbar: 'undo redo | formatselect | bold italic | alignleft aligncenter alignright | bullist numlist outdent indent | link image | table | code',
        height: 300,
        setup: function(editor) {
            editor.on('change', function() {
                editor.save();
            });
        }
    });

    // 初始化所有模态框
    const groupModal = new bootstrap.Modal(document.getElementById('groupModal'));
    const memberModal = new bootstrap.Modal(document.getElementById('memberModal'));
    const importModal = new bootstrap.Modal(document.getElementById('importModal'));

    // 拖拽相关变量
    let draggedItem = null;

    // 初始化拖拽功能
    function initDragAndDrop() {
        const draggableItems = document.querySelectorAll('.member-item.draggable');
        const dropZones = document.querySelectorAll('.member-container.droppable');

        draggableItems.forEach(item => {
            item.addEventListener('dragstart', handleDragStart);
            item.addEventListener('dragend', handleDragEnd);
        });

        dropZones.forEach(zone => {
            zone.addEventListener('dragover', handleDragOver);
            zone.addEventListener('dragenter', handleDragEnter);
            zone.addEventListener('dragleave', handleDragLeave);
            zone.addEventListener('drop', handleDrop);
        });
    }

    // 拖拽事件处理函数
    function handleDragStart(e) {
        draggedItem = this;
        this.classList.add('dragging');
        e.dataTransfer.setData('text/plain', this.dataset.memberId);
    }

    function handleDragEnd(e) {
        this.classList.remove('dragging');
        draggedItem = null;
        document.querySelectorAll('.member-container.droppable').forEach(container => {
            container.classList.remove('drag-over');
        });
    }

    function handleDragOver(e) {
        e.preventDefault();
    }

    function handleDragEnter(e) {
        e.preventDefault();
        this.classList.add('drag-over');
    }

    function handleDragLeave(e) {
        this.classList.remove('drag-over');
    }

    function handleDrop(e) {
        e.preventDefault();
        this.classList.remove('drag-over');

        const memberId = e.dataTransfer.getData('text/plain');
        const targetGroupId = this.dataset.groupId;
        const sourceGroupId = draggedItem.closest('.member-container').dataset.groupId;

        if (sourceGroupId === targetGroupId) return;

        // 检查目标组是否已满
        if (!this.classList.contains('ungrouped') && this.children.length >= 5) {
            alert('该小组已达到最大人数限制（5人）');
            return;
        }

        // 发送请求到服务器
        fetch('/api/members/move', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                member_id: memberId,
                target_group_id: targetGroupId
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || '移动失败');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // 更新 UI
                this.appendChild(draggedItem);
                updateMemberCounts(sourceGroupId, targetGroupId);
            } else {
                throw new Error(data.error || '移动失败');
            }
        })
        .catch(error => {
            alert('移动成员失败: ' + error.message);
        });
    }

    // 更新成员数量显示
    function updateMemberCounts(sourceGroupId, targetGroupId) {
        [sourceGroupId, targetGroupId].forEach(groupId => {
            const container = document.querySelector(`.member-container[data-group-id="${groupId}"]`);
            const memberCount = container.querySelector('.member-count');
            if (memberCount) {
                const total = container.querySelectorAll('.member-item').length;
                const completed = container.querySelectorAll('.member-item .badge.bg-success').length;
                memberCount.textContent = `成员：${total}/5 | 完成：${completed}/${total}`;
            }
        });
    }

    // 状态切换处理
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('status-badge')) {
            const memberId = e.target.dataset.memberId;
            const currentStatus = e.target.classList.contains('bg-success');
            
            fetch('/api/members/status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    member_id: memberId,
                    status: !currentStatus
                })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || '更新状态失败');
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    const badge = e.target;
                    if (currentStatus) {
                        badge.classList.replace('bg-success', 'bg-secondary');
                        badge.textContent = '未完成';
                    } else {
                        badge.classList.replace('bg-secondary', 'bg-success');
                        badge.textContent = '已完成';
                    }
                    
                    // 更新组的完成人数
                    const groupId = badge.closest('.member-container').dataset.groupId;
                    const container = document.querySelector(`.member-container[data-group-id="${groupId}"]`);
                    const memberCount = container.closest('.card').querySelector('.member-count');
                    if (memberCount) {
                        const total = container.querySelectorAll('.member-item').length;
                        const completed = container.querySelectorAll('.badge.bg-success').length;
                        memberCount.textContent = `成员：${total}/5 | 完成：${completed}/${total}`;
                    }
                } else {
                    throw new Error(data.error || '更新状态失败');
                }
            })
            .catch(error => {
                alert('更新状态失败: ' + error.message);
            });
        }
    });

    // 删除成员处理
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-member')) {
            if (!confirm('确定要删除该成员吗？')) return;
            
            const memberItem = e.target.closest('.member-item');
            const memberId = memberItem.dataset.memberId;
            const groupId = memberItem.closest('.member-container').dataset.groupId;
            
            fetch('/api/members/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ member_id: memberId })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || '删除失败');
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    memberItem.remove();
                    // 更新组的成员数量
                    const container = document.querySelector(`.member-container[data-group-id="${groupId}"]`);
                    const memberCount = container.closest('.card').querySelector('.member-count');
                    if (memberCount) {
                        const total = container.querySelectorAll('.member-item').length;
                        const completed = container.querySelectorAll('.badge.bg-success').length;
                        memberCount.textContent = `成员：${total}/5 | 完成：${completed}/${total}`;
                    }
                } else {
                    throw new Error(data.error || '删除失败');
                }
            })
            .catch(error => {
                alert('删除成员失败: ' + error.message);
            });
        }
    });

    // 初始化拖拽功能
    initDragAndDrop();
});
