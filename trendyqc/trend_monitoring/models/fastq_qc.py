from django.db import models


class Fastqc(models.Model):
    fastqc_read_data = models.ForeignKey("Fastqc_read_data", on_delete=models.DO_NOTHING)


class Fastqc_read_data(models.Model):
    sample_read = models.CharField(max_length=50)
    lane = models.CharField(max_length=20)
    file_type = models.CharField(max_length=50)
    encoding = models.CharField(max_length=50)
    total_sequences = models.FloatField()
    sequences_flagged_as_poor_quality = models.FloatField()
    sequence_length = models.FloatField()
    gc_pct = models.FloatField()
    total_deduplicated_pct = models.FloatField()
    avg_sequence_length = models.FloatField()
    basic_statistics = models.CharField(max_length=10)
    per_base_sequence_quality = models.CharField(max_length=10)
    per_tile_sequence_quality = models.CharField(max_length=10)
    per_sequence_quality_score = models.CharField(max_length=10)
    per_base_sequence_content = models.CharField(max_length=10)
    per_sequence_gc_content = models.CharField(max_length=10)
    per_base_n_content = models.CharField(max_length=10)
    sequence_length_distribution = models.CharField(max_length=10)
    sequence_duplication_levels = models.CharField(max_length=10)
    overrepresented_sequences = models.CharField(max_length=10)
    adapter_content = models.CharField(max_length=10)

    class Meta:
        app_label = "trend_monitoring"
        db_table = "fastqc_data"


class Bcl2fastq_data(models.Model):
    total = models.IntegerField()
    total_yield = models.IntegerField()
    perfect_index = models.IntegerField()
    yield_Q30 = models.IntegerField()
    qscore_sum = models.IntegerField()
    r1_yield = models.IntegerField()
    r1_Q30 = models.IntegerField()
    r1_trimmed_bases = models.IntegerField()
    r2_yield = models.IntegerField()
    r2_Q30 = models.IntegerField()
    r2_trimmed_bases = models.IntegerField()
    pct_Q30 = models.FloatField()
    pct_perfect_index = models.FloatField()
    mean_qscore = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "bcl2fastq_data"
