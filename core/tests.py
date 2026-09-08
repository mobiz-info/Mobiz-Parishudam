from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Branch, StaffProfile

class CoreSystemTests(TestCase):
    def setUp(self):
        # Create branch
        self.branch = Branch.objects.create(branch_code='TEST001', name='Test Branch', status='active')
        
        # Create users
        self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass123')
        self.admin_profile = StaffProfile.objects.create(user=self.admin, role='ADMIN', status='active')

        self.staff_user = User.objects.create_user('staff1', 'staff@test.com', 'pass123')
        self.staff_profile = StaffProfile.objects.create(user=self.staff_user, role='STAFF', branch=self.branch, status='active')

    def test_branch_creation(self):
        self.assertEqual(self.branch.name, 'Test Branch')
        self.assertTrue(self.branch.status, 'active')

    def test_staff_profile(self):
        self.assertTrue(self.admin_profile.is_admin)
        self.assertFalse(self.staff_profile.is_admin)
        self.assertEqual(self.staff_profile.branch, self.branch)

