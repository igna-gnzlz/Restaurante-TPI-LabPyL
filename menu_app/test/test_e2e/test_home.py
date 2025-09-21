from playwright.sync_api import expect
from menu_app.test.test_e2e.base import BaseE2ETest

class HomePageDisplayTest(BaseE2ETest):
    """Tests relacionados con la visualización de la página de inicio"""

    def test_home_page_loads(self):
        """Test que verifica que la home carga correctamente"""
        self.page.goto(f"{self.live_server_url}/")

        # Verificar que el logo esté presente y apunte a la página principal
        logo = self.page.get_by_role("link", name="Restaurante").first
        expect(logo).to_be_visible()
        expect(logo).to_have_attribute("href", "/")

        # Verificar textos principales de la página
        expect(self.page.get_by_text("Restaurante Fueguino")).to_be_visible()
        expect(self.page.get_by_text("Sabor y calidez en cada plato")).to_be_visible()
        expect(self.page.get_by_text("Reservas fáciles y rápidas")).to_be_visible()
        expect(self.page.get_by_text("Pedidos personalizados a tu gusto")).to_be_visible()
        expect(self.page.get_by_text("Atención amigable y profesional")).to_be_visible()

        # Verificar botones principales
        reservar_btn = self.page.get_by_role("link", name="Reservar Mesa")
        expect(reservar_btn).to_be_visible()
        expect(reservar_btn).to_have_attribute("href", "/bookings/make_reservation")  # Ajusta la URL si es diferente

        explorar_btn = self.page.get_by_role("link", name="Explorar Menú")
        expect(explorar_btn).to_be_visible()
        expect(explorar_btn).to_have_attribute("href", "/menu/")  # Ajusta según tu URL de menú
