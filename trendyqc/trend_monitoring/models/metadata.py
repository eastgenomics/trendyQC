from django.db import models


class Report(models.Model):
    name = models.CharField(max_length=500)
    project_id = models.CharField(max_length=50)
    project_name = models.CharField(max_length=500)
    dnanexus_file_id = models.CharField(max_length=62)
    sequencer_id = models.CharField(max_length=20)
    date = models.DateField()
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
    patient = models.ForeignKey(
        Patient, on_delete=models.DO_NOTHING, blank=True, null=True
    )
    sample_id = models.CharField(max_length=100)

    class Meta:
        app_label = "trend_monitoring"
        db_table = "sample"


class Report_Sample(models.Model):
    assay = models.CharField(max_length=50)
    report = models.ForeignKey(Report, on_delete=models.DO_NOTHING)
    sample = models.ForeignKey(Sample, on_delete=models.DO_NOTHING)
    # fastq level qc
    bcl2fastq_data = models.ForeignKey(
        "Bcl2fastq_data", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    fastqc = models.ForeignKey(
        "Fastqc", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    # bam level qc
    custom_coverage = models.ForeignKey(
        "Custom_coverage", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    verifybamid_data = models.ForeignKey(
        "VerifyBAMid_data", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    samtools_data = models.ForeignKey(
        "Samtools_data", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    picard = models.ForeignKey(
        "Picard", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    rna_seqc = models.ForeignKey(
        "RNA_seqc", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    # vcf level qc
    somalier_data = models.ForeignKey(
        "Somalier_data", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    sompy_data = models.ForeignKey(
        "Sompy_data", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    vcfqc_data = models.ForeignKey(
        "Vcfqc_data", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    happy = models.ForeignKey(
        "Happy", on_delete=models.DO_NOTHING, blank=True, null=True
    )

    class Meta:
        app_label = "trend_monitoring"
        db_table = "report_sample"
