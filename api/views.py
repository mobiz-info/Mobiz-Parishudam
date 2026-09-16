from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from operations.models import Expense
from rest_framework.decorators import action
from django.http import HttpResponse
from openpyxl import Workbook
from core.models import Branch, StaffProfile, Product, ProductPackingSize,ProductMargin
from operations.models import Vehicle

from api.serializers import (
    UserSerializer, StaffProfileSerializer, BranchSerializer,ProductSerializer,
    ProductPackingSizeSerializer,ProductMarginSerializer,VehicleSerializer,ExpenseSerializer,

)

class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user:
            if hasattr(user, 'profile') and user.profile.status == 'inactive':
                return Response({'detail': 'User account is inactive'}, status=status.HTTP_403_FORBIDDEN)
            refresh = RefreshToken.for_user(user)
            role = user.profile.role if hasattr(user, 'profile') else ('ADMIN' if user.is_superuser else 'STAFF')
            branch_id = user.profile.branch.id if hasattr(user, 'profile') and user.profile.branch else None

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': role,
                    'branch_id': branch_id
                }
            })
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class MeAPIView(APIView):
    def get(self, request):
        profile = getattr(request.user, 'profile', None)
        serializer = StaffProfileSerializer(profile) if profile else None
        return Response({
            'user': UserSerializer(request.user).data,
            'profile': serializer.data if serializer else None
        })


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer


class StaffProfileViewSet(viewsets.ModelViewSet):
    queryset = StaffProfile.objects.select_related('user', 'branch').all()
    serializer_class = StaffProfileSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductPackingSizeViewSet(viewsets.ModelViewSet):
    queryset = ProductPackingSize.objects.select_related('product').all()
    serializer_class = ProductPackingSizeSerializer

class ProductMarginViewSet(viewsets.ModelViewSet):
    queryset = ProductMargin.objects.select_related('product', 'packing_size').all()
    serializer_class = ProductMarginSerializer
class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.select_related('branch').all()
    serializer_class = VehicleSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        branch_id = self.request.query_params.get('branch')

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        return queryset


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.select_related(
        'branch',
        'staff',
        'expense_head'
    ).all()
    serializer_class = ExpenseSerializer

    @action(detail=False, methods=['get'], url_path='export')
    def export_excel(self, request):
        expenses = self.get_queryset()

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Expenses"

        headers = [
            "ID",
            "Branch",
            "Staff",
            "Expense Date",
            "Expense Head",
            "Amount",
            "Description",
        ]

        worksheet.append(headers)

        for expense in expenses:
            worksheet.append([
                expense.id,
                expense.branch.name,
                expense.staff.username if expense.staff else "",
                expense.expense_date,
                expense.expense_head.name,
                float(expense.amount),
                expense.description,
            ])

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        response["Content-Disposition"] = 'attachment; filename="expenses.xlsx"'

        workbook.save(response)

        return response