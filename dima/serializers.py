from rest_framework import serializers
from dima.models import OrgDate, Doc


class Tro(serializers.ModelSerializer):
    class Meta:
        model = Doc
        fields = ('url_doc', 'update_date')

class Lo(serializers.ModelSerializer):

    pep = Tro(many=True)

    class Meta:
        model = OrgDate
        fields = ('name', 'inn', 'id_ogr', 'url_pars', 'pep')



    def create(self, validated_data):
        tracks_data = validated_data.pop('pep')
        album = OrgDate.objects.create(**validated_data)
        for track_data in tracks_data:
            Doc.objects.create(trun=album, **track_data)
        return album






