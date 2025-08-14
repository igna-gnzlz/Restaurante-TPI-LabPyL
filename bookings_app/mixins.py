from django.contrib.auth.mixins import UserPassesTestMixin


class ClienteRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(name="Cliente").exists()
