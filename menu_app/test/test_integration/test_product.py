from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from menu_app.models import Product, Category


class BaseProductTestCase(TestCase):
    """Clase base con la configuración común para todos los tests de productos"""

    def setUp(self):
        fake_image = SimpleUploadedFile(
            name="test.jpg", content=b"file_content", content_type="image/jpeg"
        )

        # Crear categoría activa
        self.category = Category.objects.create(name="Categoría 1", isActive=True)

        # Crear productos de prueba asociados a la categoría
        self.product1 = Product.objects.create(
            name="Producto 1",
            description="Descripción del producto 1",
            price=10,
            quantity=15,
            image=fake_image,
            category=self.category
        )

        self.product2 = Product.objects.create(
            name="Producto 2",
            description="Descripción del producto 2",
            price=20,
            quantity=1,
            image=fake_image,
            category=self.category
        )

        # Cliente para hacer peticiones
        self.client = Client()


class ProductsListViewTest(BaseProductTestCase):
    """Tests para la vista de listado de productos"""

    def test_products_view(self):
        """Test que verifica que la vista products funciona"""
        response = self.client.get(reverse("menu_app:menu"))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "menu_app/menu.html")
        self.assertIn("categorized_items", response.context)

        # Obtener todos los productos de todas las categorías
        categorized_items = response.context["categorized_items"]
        all_products = []
        for products in categorized_items.values():
            all_products.extend(products)

        # Verificar que hay 2 productos en total
        self.assertEqual(len(all_products), 2)

        # Verificar que los productos están ordenados por id
        self.assertEqual(all_products[0].id, self.product1.id)
        self.assertEqual(all_products[1].id, self.product2.id)


class ProductDetailViewTest(BaseProductTestCase):
    """Tests para la vista de detalle de un producto"""

    def test_product_detail_view(self):
        """Test que verifica que la vista product_detail funciona"""
        response = self.client.get(reverse("menu_app:product_detail", args=[self.product1.id]))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "menu_app/product_detail.html")
        self.assertIn("product", response.context)
        self.assertEqual(response.context["product"].id, self.product1.id)
