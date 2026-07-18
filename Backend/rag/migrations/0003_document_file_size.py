from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rag", "0002_documentchunk_embedding"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="file_size",
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]