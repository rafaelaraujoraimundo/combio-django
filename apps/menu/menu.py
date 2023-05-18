from menu.models import GrupoMenu, ItensMenu


def GetGroup():
    groupMenu = GrupoMenu.objects.all()
    return groupMenu


def GetMenu():
    itensmenu = ItensMenu.objects.all()
    return itensmenu
