from django.contrib.auth.mixins import UserPassesTestMixin


class ClienteRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(name="Cliente").exists()


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return (
            self.request.user.is_active
            and self.request.user.is_staff
            and self.request.user.has_perm('bookings_app.change_timeslot')
        )
