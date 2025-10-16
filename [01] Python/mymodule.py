def calculate_average(numbers):
    # Check if the list is empty
    if not numbers:
        return 0

    # Calculate the sum of the numbers
    total = sum(numbers)

    # Calculate the average
    average = total / len(numbers)
    return average

def calculate_sum(numbers):
    if not numbers:
        return 0
    
    total = sum(numbers)
    return total