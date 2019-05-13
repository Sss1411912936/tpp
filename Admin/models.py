from django.contrib.auth.hashers import make_password, check_password
from django.db import models


# Create your models here.


class AdminUser(models.Model):
    a_username = models.CharField(max_length=16, unique=True)
    a_password = models.CharField(max_length=256)
    is_delete = models.BooleanField(default=False)
    is_super = models.BooleanField(default=False)

    # make_password密码加密
    def set_password(self, password):
        self.a_password = make_password(password)

    # 检查密码是否一致check_password(未加密密码，数据库保存的加密密码)
    def check_admin_password(self, password):
        print('---------')
        print(password)
        print(self.a_password)
        return check_password(password, self.a_password)

    # 判定自己有没有某个权限
    def has_permission(self,permission_name):
        permissions = self.permission_set.all()

        for permission in permissions:
            if permission_name == permission.p_name:
                return True

        return False


# 建立权限模型，多表及联实现权限设置
# 用户和权限是多对多关系
# 主从数据（谁声明谁就是从数据）比如：用户和权限，用户就是主
class Permission(models.Model):
    p_name = models.CharField(max_length=32,unique=True)
    # 多对多关系
    p_user = models.ManyToManyField(AdminUser)







