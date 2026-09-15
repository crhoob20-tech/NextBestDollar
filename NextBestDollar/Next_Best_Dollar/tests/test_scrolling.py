import unittest
from types import SimpleNamespace
from unittest.mock import patch
import ui
class ScrollTests(unittest.TestCase):
    def test_scroll_over_input_moves_page_without_native_edit(self):
        class Canvas:
            master=None
            def yview(self):return (0,0.5)
            def configure(self,**kw):pass
            def yview_scroll(self,*args):self.movement=args
        class Root:
            def __init__(self):self.handlers={};self.tk=SimpleNamespace(call=lambda *args:'aqua')
            def bind_class(self,cls,event,fn):self.handlers[cls,event]=fn
            def bind_all(self,*args,**kw):pass
        root=Root();ui.install_scrolling(root)
        with patch.object(ui.tk,'Canvas',Canvas):
            for cls in ('TCombobox','Entry','Spinbox','Text'):
                page=Canvas();field=SimpleNamespace(master=page)
                result=root.handlers[cls,'<MouseWheel>'](SimpleNamespace(widget=field,delta=-1,num=0))
                self.assertEqual(result,'break');self.assertEqual(page.movement,(1,'units'))
    def test_speed_cap(self):
        self.assertEqual(ui.wheel_units(100,'aqua'),-2)
        self.assertEqual(ui.wheel_units(0,'aqua'),0)
