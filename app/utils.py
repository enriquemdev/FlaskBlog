def form_errors(*args):
  errors = {}
  for field in args:
     errors[field] = None
  errors['blank'] = 'This field must not be blank'
  return errors