from django.db import models


class Somalier_data(models.Model):
    paternal_id = models.CharField(max_length=50)
    maternal_id = models.CharField(max_length=50)
    family_id = models.CharField(max_length=100)
    sex = models.FloatField()
    phenotype = models.FloatField()
    original_pedigree_sex = models.CharField(max_length=10)
    gt_depth_mean = models.FloatField()
    gt_depth_sd = models.FloatField(null=True)
    depth_mean = models.FloatField()
    depth_sd = models.FloatField()
    ab_mean = models.FloatField()
    ab_std = models.FloatField(null=True)
    nb_hom_ref = models.FloatField()
    nb_het = models.FloatField()
    nb_hom_alt = models.FloatField()
    nb_unknown = models.FloatField()
    p_middling_ab = models.FloatField()
    x_depth_mean = models.FloatField()
    x_nb = models.FloatField()
    x_hom_ref = models.FloatField()
    x_het = models.FloatField()
    x_hom_alt = models.FloatField()
    y_depth_mean = models.FloatField()
    y_nb = models.FloatField()
    predicted_sex = models.CharField(max_length=10)
    match_sexes = models.CharField(max_length=5, null=True)

    class Meta:
        app_label = "trend_monitoring"
        db_table = "somalier_data"


class Sompy_data(models.Model):
    indels_total_truth = models.FloatField()
    indels_total_query = models.FloatField()
    indels_tp = models.FloatField()
    indels_fp = models.FloatField()
    indels_fn = models.FloatField()
    indels_unk = models.FloatField()
    indels_ambi = models.FloatField()
    indels_recall = models.FloatField()
    indels_recall_lower = models.FloatField()
    indels_recall_upper = models.FloatField()
    indels_recall2 = models.FloatField()
    indels_precision = models.FloatField()
    indels_precision_lower = models.FloatField()
    indels_precision_upper = models.FloatField()
    indels_na = models.FloatField()
    indels_ambiguous = models.FloatField()
    indels_fp_region_size = models.FloatField()
    indels_fp_rate = models.FloatField()
    snvs_total_truth = models.FloatField()
    snvs_total_query = models.FloatField()
    snvs_tp = models.FloatField()
    snvs_fp = models.FloatField()
    snvs_fn = models.FloatField()
    snvs_unk = models.FloatField()
    snvs_ambi = models.FloatField()
    snvs_recall = models.FloatField()
    snvs_recall_lower = models.FloatField()
    snvs_recall_upper = models.FloatField()
    snvs_recall2 = models.FloatField()
    snvs_precision = models.FloatField()
    snvs_precision_lower = models.FloatField()
    snvs_precision_upper = models.FloatField()
    snvs_na = models.FloatField()
    snvs_ambiguous = models.FloatField()
    snvs_fp_region_size = models.FloatField()
    snvs_fp_rate = models.FloatField()
    records_total_truth = models.FloatField()
    records_total_query = models.FloatField()
    records_tp = models.FloatField()
    records_fp = models.FloatField()
    records_fn = models.FloatField()
    records_unk = models.FloatField()
    records_ambi = models.FloatField()
    records_recall = models.FloatField()
    records_recall_lower = models.FloatField()
    records_recall_upper = models.FloatField()
    records_recall2 = models.FloatField()
    records_precision = models.FloatField()
    records_precision_lower = models.FloatField()
    records_precision_upper = models.FloatField()
    records_na = models.FloatField()
    records_ambiguous = models.FloatField()
    records_fp_region_size = models.FloatField()
    records_fp_rate = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "sompy_data"


class Vcfqc_data(models.Model):
    mean_het_ratio = models.FloatField()
    mean_hom_ratio = models.FloatField()
    het_hom_ratio = models.FloatField()
    x_het_hom_ratio = models.FloatField()
    gender = models.CharField(max_length=10, null=True)

    class Meta:
        app_label = "trend_monitoring"
        db_table = "vcfqc_data"


class Happy(models.Model):
    happy_snp_all = models.ForeignKey(
        "Happy_snp_all", on_delete=models.DO_NOTHING, null=True
    )
    happy_snp_pass = models.ForeignKey(
        "Happy_snp_pass", on_delete=models.DO_NOTHING, null=True
    )
    happy_indel_all = models.ForeignKey(
        "Happy_indel_all", on_delete=models.DO_NOTHING, null=True
    )
    happy_indel_pass = models.ForeignKey(
        "Happy_indel_pass", on_delete=models.DO_NOTHING, null=True
    )

    class Meta:
        app_label = "trend_monitoring"
        db_table = "happy"


class Happy_snp_all(models.Model):
    filter_snp = models.CharField(max_length=10)
    truth_total_snp = models.IntegerField()
    truth_tp_snp = models.IntegerField()
    truth_fn_snp = models.IntegerField()
    query_total_snp = models.IntegerField()
    query_fp_snp = models.IntegerField()
    query_unk_snp = models.IntegerField()
    fp_gt_snp = models.IntegerField()
    metric_recall_snp = models.FloatField()
    metric_precision_snp = models.FloatField()
    metric_frac_na_snp = models.FloatField()
    metric_f1_score_snp = models.FloatField()
    truth_total_titv_ratio_snp = models.FloatField(null=True)
    query_total_titv_ratio_snp = models.FloatField(null=True)
    truth_total_het_hom_ratio_snp = models.FloatField()
    query_total_het_hom_ratio_snp = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "happy_snp_all"


class Happy_snp_pass(models.Model):
    filter_snp = models.CharField(max_length=10)
    truth_total_snp = models.IntegerField()
    truth_tp_snp = models.IntegerField()
    truth_fn_snp = models.IntegerField()
    query_total_snp = models.IntegerField()
    query_fp_snp = models.IntegerField()
    query_unk_snp = models.IntegerField()
    fp_gt_snp = models.IntegerField()
    metric_recall_snp = models.FloatField()
    metric_precision_snp = models.FloatField()
    metric_frac_na_snp = models.FloatField()
    metric_f1_score_snp = models.FloatField()
    truth_total_titv_ratio_snp = models.FloatField(null=True)
    query_total_titv_ratio_snp = models.FloatField(null=True)
    truth_total_het_hom_ratio_snp = models.FloatField()
    query_total_het_hom_ratio_snp = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "happy_snp_pass"


class Happy_indel_all(models.Model):
    filter_indel = models.CharField(max_length=10)
    truth_total_indel = models.IntegerField()
    truth_tp_indel = models.IntegerField()
    truth_fn_indel = models.IntegerField()
    query_total_indel = models.IntegerField()
    query_fp_indel = models.IntegerField()
    query_unk_indel = models.IntegerField()
    fp_gt_indel = models.IntegerField()
    metric_recall_indel = models.FloatField()
    metric_precision_indel = models.FloatField()
    metric_frac_na_indel = models.FloatField()
    metric_f1_score_indel = models.FloatField()
    truth_total_titv_ratio_indel = models.FloatField(null=True)
    query_total_titv_ratio_indel = models.FloatField(null=True)
    truth_total_het_hom_ratio_indel = models.FloatField()
    query_total_het_hom_ratio_indel = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "happy_indel_all"


class Happy_indel_pass(models.Model):
    filter_indel = models.CharField(max_length=10)
    truth_total_indel = models.IntegerField()
    truth_tp_indel = models.IntegerField()
    truth_fn_indel = models.IntegerField()
    query_total_indel = models.IntegerField()
    query_fp_indel = models.IntegerField()
    query_unk_indel = models.IntegerField()
    fp_gt_indel = models.IntegerField()
    metric_recall_indel = models.FloatField()
    metric_precision_indel = models.FloatField()
    metric_frac_na_indel = models.FloatField()
    metric_f1_score_indel = models.FloatField()
    truth_total_titv_ratio_indel = models.FloatField(null=True)
    query_total_titv_ratio_indel = models.FloatField(null=True)
    truth_total_het_hom_ratio_indel = models.FloatField()
    query_total_het_hom_ratio_indel = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "happy_indel_pass"
