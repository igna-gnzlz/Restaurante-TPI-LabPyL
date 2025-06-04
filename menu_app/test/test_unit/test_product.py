from django.test import TestCase

from django.core.files.uploadedfile import SimpleUploadedFile

from menu_app.models import Product


class ProductModelTest(TestCase):
    def test_product_creation(self):
        product = Product.objects.create(
            name="Producto de prueba",
            description="Descripción del producto de prueba",
            price=10,
            quantity=15,
        )
        """Test que verifica la creación correcta de productos"""
        self.assertEqual(product.name, "Producto de prueba")
        self.assertEqual(product.description, "Descripción del producto de prueba")
        self.assertEqual(product.price, float(10))
        self.assertEqual(product.quantity, 15)

    def test_product_validate_with_valid_data(self):
        """Test que verifica la validación de productos con datos válidos"""
        errors = Product.validate("Título válido", "Descripción válida", 10)
        self.assertEqual(errors, {})

    def test_product_validate_with_empty_name(self):
        """Test que verifica la validación de productos con título vacío"""
        errors = Product.validate("", "Descripción válida", 10)
        self.assertIn("name", errors)
        self.assertEqual(errors["name"], "Por favor ingrese un nombre")

    def test_product_validate_with_empty_description(self):
        """Test que verifica la validación de productos con descripción vacía"""
        errors = Product.validate("Título válido", "", 10)
        self.assertIn("description", errors)
        self.assertEqual(errors["description"], "Por favor ingrese una descripción")

    def test_product_new_with_valid_data(self):
        """Test que verifica la creación de productos con datos válidos"""

        fake_image = SimpleUploadedFile(
            name="test.jpg", content=b"file_content", content_type="image/jpeg"
        )

        success, errors = Product.new(
            name="Nuevo producto",
            description="Descripción del nuevo producto",
            price=10,
            quantity=15,
            image=fake_image,
        )

        self.assertTrue(success)
        self.assertIsNone(errors)

        # Verificar que el producto fue creado en la base de datos
        new_product = Product.objects.get(name="Nuevo producto")
        self.assertEqual(new_product.description, "Descripción del nuevo producto")

    def test_product_new_with_invalid_data(self):
        """Test que verifica que no se crean productos con datos inválidos"""
        initial_count = Product.objects.count()

        fake_image = SimpleUploadedFile(
            name="test.jpg", content=b"file_content", content_type="image/jpeg"
        )

        # Intentar crear producto con título vacío
        success, errors = Product.new(
            name="",
            description="Descripción del producto",
            price=10,
            quantity=15,
            image=fake_image,
        )

        self.assertFalse(success)
        self.assertIn("name", errors)

        # Verificar que no se creó ningún producto nuevo
        self.assertEqual(Product.objects.count(), initial_count)

    def test_product_update(self):
        """Test que verifica la actualización de productos"""
        new_name = "Título actualizado"
        new_description = "Descripción actualizada"
        new_price = 2
        new_quantity = 10

        product = Product.objects.create(
            name="Producto de prueba",
            description="Descripción del producto de prueba",
            price=10,
            quantity=15,
        )

        product.update(
            name=new_name,
            description=new_description,
            price=new_price,
            quantity=new_quantity,
        )

        # Recargar el producto desde la base de datos
        updated_product = Product.objects.get(pk=product.pk)

        self.assertEqual(updated_product.name, new_name)
        self.assertEqual(updated_product.description, new_description)
        self.assertEqual(updated_product.price, new_price)
        self.assertEqual(updated_product.quantity, new_quantity)

    def test_product_update_partial(self):
        """Test que verifica la actualización parcial de productos"""
        product = Product.objects.create(
            name="Producto de prueba",
            description="Descripción del producto de prueba",
            price=10,
            quantity=15,
        )

        original_name = product.name
        original_price = product.price
        original_quantity = product.quantity
        new_description = "Solo la descripción ha cambiado"

        product.update(
            name=None,  # No cambiar
            description=new_description,
            price=None,  # No cambiar
            quantity=None,  # No cambiar
        )

        # Recargar el producto desde la base de datos
        updated_product = Product.objects.get(pk=product.pk)

        # Verificar que solo cambió la descripción
        self.assertEqual(updated_product.name, original_name)
        self.assertEqual(updated_product.description, new_description)
        self.assertEqual(updated_product.price, original_price)
        self.assertEqual(updated_product.quantity, original_quantity)
