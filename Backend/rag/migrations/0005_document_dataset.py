from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rag", "0004_alter_documentchunk_embedding"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="dataset",
            field=models.CharField(
                blank=True,
                default="default",
                help_text="Dataset or collection name for multi-dataset support",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="document",
            name="language",
            field=models.CharField(
                blank=True,
                default="en",
                help_text="ISO 639-1 language code for multilingual support",
                max_length=10,
            ),
        ),
    ]