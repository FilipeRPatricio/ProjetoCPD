def is_prime(n: int) -> bool:
 if n < 2:
    return False
 if n in (2, 3):
  return True
 if n % 2 == 0 or n % 3 == 0:
  return False

 divisor = 5
 while divisor * divisor <= n:
  if n % divisor == 0 or n % (divisor + 2) == 0:
   return False
  divisor += 6
 return True