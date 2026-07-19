from django.db import migrations
# Ensure this import is exactly like this:
import pgvector
from pgvector.django import VectorExtension 

class Migration(migrations.Migration):

    dependencies = [
        ('rag', '0003_document_file_size'),
    ]

    operations = [
        # Change PgVectorExtension() to VectorExtension()
        VectorExtension(), 
        
        migrations.RunSQL(
            sql='ALTER TABLE rag_documentchunk ALTER COLUMN embedding TYPE vector(1536) USING embedding::text::vector(1536);',
            reverse_sql='ALTER TABLE rag_documentchunk ALTER COLUMN embedding TYPE jsonb USING embedding::text::jsonb;'
        ),
        
        migrations.AlterField(
            model_name='documentchunk',
            name='embedding',
            field=pgvector.django.VectorField(blank=True, dimensions=1536, null=True),
        ),
    ]