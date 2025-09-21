from playwright.sync_api import expect

from menu_app.models import Product, Category

from django.core.files.uploadedfile import SimpleUploadedFile

from menu_app.test.test_e2e.base import BaseE2ETest


class ProductBaseTest(BaseE2ETest):
    """Clase base específica para tests de productos"""

    def setUp(self):
        super().setUp()
        fake_image = SimpleUploadedFile(
            name="test.jpg", content=b"file_content", content_type="image/jpeg"
        )

        # Crear categoría de prueba
        self.category = Category.objects.create(name="Categoría de prueba")

        # Producto 1 con categoría
        self.product1 = Product.objects.create(
            name="Producto de prueba 1",
            description="Descripción del producto 1",
            price=10,
            quantity=15,
            image=fake_image,
            category=self.category
        )

        # Producto 2 con categoría
        self.product2 = Product.objects.create(
            name="Producto de prueba 2",
            description="Descripción del producto 2",
            price=11,
            quantity=0,
            image=fake_image,
            category=self.category
        )

    def _table_has_product_info(self):
        """Método auxiliar para verificar que la lista tiene la información correcta de productos"""
        expect(self.page.locator("h1")).to_have_text("Menú")

        # Verificar que los productos aparecen en la lista
        cards = self.page.locator(".item-card")
        expect(cards).to_have_count(2)

        # Verificar datos del primer producto
        expect(cards.nth(0).locator(".item-title a")).to_have_text("Producto de prueba 1")
        expect(cards.nth(0).locator("p:nth-of-type(1)")).to_have_text("Descripción del producto 1")
        expect(cards.nth(0).locator("p:nth-of-type(3) strong, p:nth-of-type(3) span")).to_have_text("$10,00")

        # Verificar datos del segundo producto
        expect(cards.nth(1).locator(".item-title a")).to_have_text("Producto de prueba 2")
        expect(cards.nth(1).locator("p:nth-of-type(1)")).to_have_text("Descripción del producto 2")
        expect(cards.nth(1).locator("p:nth-of-type(3) strong, p:nth-of-type(3) span")).to_have_text("$11,00")



class ProductDisplayTest(ProductBaseTest):
    """Tests relacionados con la visualización de la página de productos"""

    def test_products_page_display(self):
        """Test que verifica la visualización correcta de la página de productos para organizadores"""
        self.page.goto(f"{self.live_server_url}/menu/")

        # Verificar el título de la página
        expect(self.page).to_have_title("Restaurante")

        # Verificar que existe un encabezado con el texto "productos"
        header = self.page.locator("h1")
        expect(header).to_have_text("Menú")
        expect(header).to_be_visible()

        self._table_has_product_info()

    def test_products_page_no_products(self):
        """Test que verifica el comportamiento cuando no hay productos"""
        # Eliminar todos los productos
        Product.objects.all().delete()

        # Ir a la página de productos
        self.page.goto(f"{self.live_server_url}/menu/")

        # Verificar que existe un mensaje indicando que no hay productos
        no_products_message = self.page.locator("text=No hay productos disponibles")
        expect(no_products_message).to_be_visible()
