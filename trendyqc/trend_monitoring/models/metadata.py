from django.db import models


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
    # fastq qc
    bcl2fastq = models.ForeignKey(
        "Bcl2fastq_data", on_delete=models.DO_NOTHING
    )
    # bam qc
    verifyBAMid = models.ForeignKey(
        "VerifyBAMid_data", on_delete=models.DO_NOTHING
    )
    samtools = models.ForeignKey(
        "Samtools_data", on_delete=models.DO_NOTHING
    )
    picard_table = models.ForeignKey("Picard", on_delete=models.DO_NOTHING)
    # vcf qc
    somalier = models.ForeignKey(
        "Somalier_data", on_delete=models.DO_NOTHING
    )
    sompy = models.ForeignKey("Sompy_data", on_delete=models.DO_NOTHING)
    vcfqc = models.ForeignKey("Vcfqc_data", on_delete=models.DO_NOTHING)
    happy_link = models.ForeignKey("Happy", on_delete=models.DO_NOTHING)

    class Meta:
        app_label = "trend_monitoring"
        db_table = "report_sample"
