from django.db import models


class Fastqc(models.Model):
    read_data_1st_lane_R1 = models.ForeignKey(
        "Read_data", on_delete=models.DO_NOTHING,
        related_name="read_data_1st_lane_R1"
    )
    read_data_1st_lane_R2 = models.ForeignKey(
        "Read_data", on_delete=models.DO_NOTHING,
        related_name="read_data_1st_lane_R2"
    )
    read_data_2nd_lane_R1 = models.ForeignKey(
        "Read_data", on_delete=models.DO_NOTHING,
        related_name="read_data_2nd_lane_R1", blank=True, null=True
    )
    read_data_2nd_lane_R2 = models.ForeignKey(
        "Read_data", on_delete=models.DO_NOTHING,
        related_name="read_data_2nd_lane_R2", blank=True, null=True
    )


class Read_data(models.Model):
    sample_read = models.CharField(max_length=50, blank=True)
    lane = models.CharField(max_length=20, blank=True)
    file_type = models.CharField(max_length=50)
    encoding = models.CharField(max_length=50)
    total_sequences = models.FloatField()
    sequences_flagged_as_poor_quality = models.FloatField()
    sequence_length = models.CharField(max_length=20)
    gc_pct = models.FloatField()
    total_deduplicated_pct = models.FloatField()
    avg_sequence_length = models.FloatField()
    basic_statistics = models.CharField(max_length=10)
    per_base_sequence_quality = models.CharField(max_length=10)
    per_tile_sequence_quality = models.CharField(max_length=10, null=True)
    per_sequence_quality_scores = models.CharField(max_length=10)
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
    total = models.BigIntegerField(null=True)
    total_yield = models.BigIntegerField(null=True)
    perfect_index = models.BigIntegerField(null=True)
    yield_Q30 = models.BigIntegerField(null=True)
    qscore_sum = models.BigIntegerField(null=True)
    r1_yield = models.BigIntegerField(null=True)
    r1_Q30 = models.BigIntegerField(null=True)
    r1_trimmed_bases = models.BigIntegerField(null=True)
    r2_yield = models.BigIntegerField(null=True)
    r2_Q30 = models.BigIntegerField(null=True)
    r2_trimmed_bases = models.BigIntegerField(null=True)
    pct_Q30 = models.FloatField(null=True)
    pct_perfect_index = models.FloatField(null=True)
    mean_qscore = models.FloatField(null=True)

    class Meta:
        app_label = "trend_monitoring"
        db_table = "bcl2fastq_data"
