def completion(total, completed):

    if total == 0:
        return 0

    percentage = (completed / total) * 100
    return percentage


total = int(input("Enter total learning activities: "))
completed = int(input("Enter completed activities: "))

result = completion(total, completed)

print("Course Completion:", result, "%")