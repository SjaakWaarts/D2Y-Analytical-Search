import django.apps
import seeker


class AppConfig (django.apps.AppConfig):
    name = 'app'

    def ready(self):
        import seeker
        import app.models as models

        #models.ExcelDoc = seeker.mapping.document_from_model(models.ecosystem, index="excel", using=models.client)
        #seeker.register(models.ExcelDoc)
        #models.ExcelSeekerView.document = models.ExcelDoc

        models.PerfumeDoc = seeker.mapping.document_from_model(models.Perfume, index="review", using=models.client)
        seeker.register(models.PerfumeDoc)
        models.PerfumeSeekerView.document = models.PerfumeDoc

        models.PostDoc = seeker.mapping.document_from_model(models.Post, index="post", using=models.client)
        seeker.register(models.PostDoc)
        models.PostSeekerView.document = models.PostDoc

        models.PageDoc = seeker.mapping.document_from_model(models.Page, index="page", using=models.client)
        seeker.register(models.PageDoc)
        models.PageSeekerView.document = models.PageDoc

        models.FeedlyDoc = seeker.mapping.document_from_model(models.Feedly, index="feedly", using=models.client)
        seeker.register(models.FeedlyDoc)
        models.FeedlySeekerView.document = models.FeedlyDoc

        models.ScentemotionDoc = seeker.mapping.document_from_model(models.Scentemotion, index="scentemotion", using=models.client)
        seeker.register(models.ScentemotionDoc)
        models.ScentemotionSeekerView.document = models.ScentemotionDoc

        models.StudiesDoc = seeker.mapping.document_from_model(models.Studies, index="studies", using=models.client)
        seeker.register(models.StudiesDoc)
        models.StudiesSeekerView.document = models.StudiesDoc

        models.SurveyDoc = seeker.mapping.document_from_model(models.Survey, index="survey", using=models.client)
        seeker.register(models.SurveyDoc)
        models.SurveySeekerView.document = models.SurveyDoc
        pass

