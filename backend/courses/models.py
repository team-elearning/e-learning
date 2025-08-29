from django.db import models

# Create your models here.
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    instructor = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                                   related_name='courses_taught',
                                   limit_choices_to={'role': 'instructor'})
    students = models.ManyToManyField('accounts.User', 
                                      related_name='courses_enrolled',
                                      blank=True,
                                      limit_choices_to={'role': 'student'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, 
                               related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('course', 'order')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Enrollment(models.Model):
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                                related_name='enrollments',
                                limit_choices_to={'role': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, 
                               related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # percentage
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'course')
    
    def __str__(self):
        return f"{self.student.email} enrolled in {self.course.title}"
