"""Gera as capturas genéricas do README (docs/images/).

Uso: python tools/readme_screenshots.py [pasta]   (por omissão docs/images)
Corre sem Windows: Qt offscreen e plataforma simulada, com macros de exemplo
em inglês e uma pasta de configuração temporária."""
import os
import pathlib
import sys
import tempfile
os.environ["QT_QPA_PLATFORM"]="offscreen"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
qa=QApplication([]); qa.setFont(QFont("DejaVu Sans", 9))
from macropad.platform.dummy import DummyPlatform
from macropad.ui.app import MacropadApp
from macropad.core.model import Macro
out=pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "docs/images"); out.mkdir(parents=True, exist_ok=True)
root=pathlib.Path(tempfile.mkdtemp())
a=MacropadApp(qa, root, DummyPlatform())
s=a.store.settings.clone(); s.idioma="en"; s.tema="diurno"; a.store.save_settings(s); a.apply_config()
ms=a.store.sets["predefinido"].clone()
ms.nome="Everyday"
ms.macros=[Macro("Greeting","1","Hello,{Enter}{Enter}"), Macro("Thanks","2","Thank you!{Enter}"),
           Macro("Sign-off","3","Best regards,{Enter}Alex"), Macro("Email","4","alex@example.com"),
           Macro("Address","F6","221B Example Street"), Macro("Tab out","F7","{Tab}{Tab}{Enter}"),
           Macro("Calls","F9",tipo="contador",id="calls"), Macro("Ticket","F8","TICKET-{Delay:200}")]
ms.macros[1].arquivada=False
ms.macros.insert(6, Macro("", "", tipo="espaco"))
ms.macros.append(Macro("Old note","","Archived text", arquivada=True))
assert a.store.save_set(ms)==[], a.store.save_set(ms)
a.apply_config()
a.set_count("predefinido","calls",12)
a.show_config(); w=a.config_window; w.resize(700, 1060); w._select(0); qa.processEvents()
w.grab().save(str(out/"settings.png"))
s=a.store.settings.clone(); s.tema="noturno"; s.painel.opacidade=0.95; a.store.save_settings(s); a.apply_config()
a.set_panel_visible(True); qa.processEvents()
a.panel.grab().save(str(out/"panel.png"))
a.quit(); print("ok")
