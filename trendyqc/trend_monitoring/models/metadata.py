from django.db import models
from .fastq_qc import Bcl2fastq_data
from .bam_qc import (
    VerifyBAMid_data, Samtools_data, Sentieon_data, Picard_hs_data
)
from .vcf_qc import Somalier_data, Sompy_data


class Report(models.Model):
    name = models.CharField(max_length=50)
    run = models.CharField(max_length=50)
    dnanexus_file_id = models.CharField(max_length=62)
    job_date = models.DateTimeField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "report"


class Patient(models.Model):
    gm_number = models.CharField(max_length=20)
    sex = models.CharField(max_length=1)

    class Meta:
        app_label = "trend_monitoring"
        db_table = "patient"


class Sample(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.DO_NOTHING)
    sample_id = models.CharField(max_length=15)

    class Meta:
        app_label = "trend_monitoring"
        db_table = "sample"


class Report_Sample(models.Model):
    assay = models.CharField(max_length=50)
    report = models.ForeignKey(Report, on_delete=models.DO_NOTHING)
    sample = models.ForeignKey(Sample, on_delete=models.DO_NOTHING)
    bcl2fastq_data = models.ForeignKey(
        Bcl2fastq_data, on_delete=models.DO_NOTHING
    )
    verifyBAMid_data = models.ForeignKey(
        VerifyBAMid_data, on_delete=models.DO_NOTHING
    )
    samtools_data = models.ForeignKey(
        Samtools_data, on_delete=models.DO_NOTHING
    )
    picard = models.ForeignKey(Picard, on_delete=models.DO_NOTHING)
    somalier_data = models.ForeignKey(
        Somalier_data, on_delete=models.DO_NOTHING
    )
    sompy_data = models.ForeignKey(Sompy_data, on_delete=models.DO_NOTHING)

    class Meta:
        app_label = "trend_monitoring"
        db_table = "report_sample"
