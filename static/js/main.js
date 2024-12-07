document.addEventListener('DOMContentLoaded', function() {
    // Initialize all group cards
    const groupContainer = document.getElementById('groupContainer');
    const groups = document.querySelectorAll('.group-card');
    let currentGroupCard = null;

    // 初始化所有模态框
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (modal) {
            new bootstrap.Modal(modal);
        }
    });

    // Group name editing
    document.querySelectorAll('.group-name').forEach(input => {
        let originalValue;

        input.addEventListener('focus', function() {
            originalValue = this.value;
            this.select();
        });

        input.addEventListener('blur', function() {
            if (this.value.trim() === '') {
                this.value = originalValue;
                return;
            }
            if (this.value !== originalValue) {
                updateGroupName(this.closest('.group-card').dataset.groupId, this.value.trim());
            }
        });

        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                this.blur();
            }
        });
    });

    // Initialize Sortable for each member list
    groups.forEach(group => {
        const memberList = group.querySelector('.member-list');
        if (memberList) {
            new Sortable(memberList, {
                group: 'members',
                animation: 150,
                dragClass: 'dragging',
                ghostClass: 'ghost',
                onStart: function(evt) {
                    evt.item.classList.add('dragging');
                },
                onEnd: function(evt) {
                    evt.item.classList.remove('dragging');
                    const memberId = evt.item.dataset.memberId;
                    const newGroupId = evt.to.closest('.group-card').dataset.groupId;
                    const oldGroupId = evt.from.closest('.group-card').dataset.groupId;
                    
                    if (newGroupId !== oldGroupId) {
                        // Check if target group is full
                        if (evt.to.children.length > 5) {
                            evt.from.appendChild(evt.item);
                            alert('该小组已达到最大人数限制（5人）');
                            return;
                        }
                        updateMemberGroup(memberId, newGroupId);
                    }
                }
            });
        }
    });

    // Add member button handling
    document.querySelectorAll('.add-member-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const groupCard = this.closest('.group-card');
            const memberList = groupCard.querySelector('.member-list');
            if (memberList.children.length >= 5) {
                alert('该小组已达到最大人数限制（5人）');
                return;
            }
            currentGroupCard = groupCard;
            const addMemberModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('memberModal'));
            addMemberModal.show();
        });
    });

    // Confirm add member
    document.getElementById('saveMember').addEventListener('click', function() {
        const memberName = document.getElementById('memberName').value.trim();
        if (!memberName) {
            alert('请输入学生姓名');
            return;
        }
        if (currentGroupCard) {
            addMemberToGroup(currentGroupCard.dataset.groupId, memberName);
            const addMemberModal = bootstrap.Modal.getInstance(document.getElementById('memberModal'));
            if (addMemberModal) {
                addMemberModal.hide();
            }
            document.getElementById('memberName').value = '';
        }
    });

    // Status toggle
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('badge')) {
            const memberItem = e.target.closest('.member-item');
            const memberName = memberItem.textContent.trim().split('\n')[0];
            const currentStatus = e.target.classList.contains('bg-success');
            const newStatus = !currentStatus;
            
            if (confirm(`确定要将 ${memberName} 的状态更改为${newStatus ? '已完成' : '未完成'}吗？`)) {
                const memberId = memberItem.dataset.memberId;
                toggleMemberStatus(memberId, newStatus);
            }
        }
    });

    // API functions
    function updateGroupName(groupId, newName) {
        if (!groupId) return;  // 如果组ID为空，不执行更新
        fetch('/api/groups', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: groupId, name: newName })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || '更新失败');
                });
            }
            return response.json();
        })
        .catch(error => {
            alert('更新组名失败: ' + error.message);
        });
    }

    function addMemberToGroup(groupId, memberName) {
        if (!groupId) {
            alert('请先创建小组');
            return;
        }
        fetch('/api/members', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ group_id: groupId, username: memberName })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || '添加失败');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                throw new Error(data.error || '添加失败');
            }
        })
        .catch(error => {
            alert(error.message);
        });
    }

    function updateMemberGroup(memberId, newGroupId) {
        fetch('/api/members/move', {  
            method: 'POST',  
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                member_id: memberId,  
                target_group_id: newGroupId  
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
                location.reload();
            } else {
                throw new Error(data.error || '移动失败');
            }
        })
        .catch(error => {
            alert('移动组员失败: ' + error.message);
            location.reload(); // 重新加载以恢复正确状态
        });
    }

    function toggleMemberStatus(memberId, newStatus) {
        fetch('/api/members/status', {  
            method: 'POST',  
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                member_id: memberId,  
                status: newStatus 
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
                location.reload();
            } else {
                throw new Error(data.error || '更新状态失败');
            }
        })
        .catch(error => {
            alert('更新状态失败: ' + error.message);
            location.reload();
        });
    }
});
