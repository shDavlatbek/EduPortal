from django.contrib.auth.models import Group

def get_group_count(group_name):
    return Group.objects.get(name=group_name).user_set.count()

students = Group.objects.get(name='student_group').user_set
teachers = Group.objects.get(name='teacher_group').user_set
admins = Group.objects.get(name='admin_group').user_set
super_admins = Group.objects.get(name='superadmin_group').user_set
