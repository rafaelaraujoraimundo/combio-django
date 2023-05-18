from django.db import models

# Create your models here.


class GrupoMenu(models.Model):
    NomeGrupo = models.CharField(max_length=40)
    icon_grupo = models.CharField(max_length=80)

    class Meta:
        db_table = 'grupoMenu'

    def __str__(self):
        return self.NomeGrupo


class ItensMenu(models.Model):
    Item = models.CharField(max_length=40)
    grupo_id = models.ForeignKey(
        GrupoMenu, on_delete=models.PROTECT)
    icon_item = models.CharField(max_length=80)
    url = models.CharField(max_length=80)

    class Meta:
        db_table = 'ItensMenu'

    def __str__(self):
        return self.Item
