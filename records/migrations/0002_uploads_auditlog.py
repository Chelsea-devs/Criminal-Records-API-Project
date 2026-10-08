from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies=[('records','0001_initial'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
      migrations.AddField(model_name='criminal',name='mugshot',field=models.ImageField(blank=True,null=True,upload_to='mugshots/%Y/%m/')),
      migrations.AddField(model_name='evidence',name='evidence_file',field=models.FileField(blank=True,null=True,upload_to='evidence/%Y/%m/')),
      migrations.CreateModel(name='AuditLog',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('action',models.CharField(choices=[('create','Created'),('update','Updated'),('delete','Deleted'),('view','Viewed'),('login','Login'),('export','Exported PDF')],max_length=20)),('object_type',models.CharField(max_length=80)),('object_reference',models.CharField(blank=True,max_length=180)),('description',models.TextField(blank=True)),('ip_address',models.GenericIPAddressField(blank=True,null=True)),('created_at',models.DateTimeField(auto_now_add=True)),('actor',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,to=settings.AUTH_USER_MODEL))],options={'ordering':['-created_at']})]
