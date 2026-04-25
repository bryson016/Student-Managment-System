# TODO - Add Default Courses & Fixes

- [x] db.py: Add `seed_courses()` to insert 6 default courses during init (removed "Application That Integrates Skills Gained Across")
- [x] db.py: Cleaned up existing database to remove unwanted course
- [x] app.py: Pass `enrolled_courses` to dashboard template and `courses` to index template
- [x] app.py: Add `/enroll-multiple` route for batch enrollment
- [x] templates/index.html: Replace hardcoded `0` with dynamic `{{ courses|length }}`
- [x] templates/base.html: Add "Courses" navigation link
- [x] templates/courses.html: Add checkbox selection + "Enroll Selected Courses" button for multi-course enrollment
- [x] Test application startup and verify courses are seeded

