from django.db import models

# Create your models here.

class Company(models.Model):
    ticker = models.CharField(max_length = 20, unique = True)

    def __str__(self):
        return self.ticker

class QuarterlyResult(models.Model):
    company = models.ForeignKey(Company, on_delete = models.CASCADE, related_name = 'quarterly_results')
    month = models.PositiveSmallIntegerField()
    year = models.PositiveIntegerField()
    sales = models.DecimalField(max_digits = 15, decimal_places = 2)
    expenses = models.DecimalField(max_digits = 15, decimal_places = 2)
    pbt = models.DecimalField(max_digits=15, decimal_places=2)  # Profit Before Tax
    pat = models.DecimalField(max_digits=15, decimal_places=2)  # Profit After Tax
    eps = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Earnings Per Share
    date_reported = models.DateField()

    class Meta:
        unique_together = ('company', 'year', 'month')

    def __str__(self):
        return f"{self.company.ticker} - {self.month:02d} - {self.year}"
    
class AnnualResult(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='annual_results')
    year = models.PositiveIntegerField()  # e.g., 2025
    sales = models.DecimalField(max_digits=15, decimal_places=2)
    expenses = models.DecimalField(max_digits=15, decimal_places=2)
    pbt = models.DecimalField(max_digits=15, decimal_places=2)
    pat = models.DecimalField(max_digits=15, decimal_places=2)
    eps = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    date_reported = models.DateField()

    class Meta:
        unique_together = ('company', 'year')

    def __str__(self):
        return f"{self.company.ticker} - {self.year}"