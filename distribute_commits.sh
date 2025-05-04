#!/bin/bash

# Script to commit and push changes one file at a time
# Distributing 23 commits across May 4-10, 2025

# Array of changed files (replace these with actual changed files)
changed_files=($(git ls-files --modified --others --exclude-standard))

# Check if we have exactly 23 files
if [ ${#changed_files[@]} -ne 23 ]; then
    echo "Warning: Found ${#changed_files[@]} files instead of 23. Proceeding anyway."
fi

# Commit messages variations
commit_prefixes=("Update" "Modify" "Change" "Revise" "Adjust" "Improve" "Fix" "Enhance" "Refine" "Tweak")
commit_suffixes=("functionality" "implementation" "code" "logic" "structure" "content" "formatting" "style" "documentation" "configuration")

# Define dates from May 4-10, 2025
dates=(
    "2025-05-04T12:00:00" 
    "2025-05-05T12:00:00" 
    "2025-05-06T12:00:00" 
    "2025-05-07T12:00:00" 
    "2025-05-08T12:00:00" 
    "2025-05-09T12:00:00" 
    "2025-05-10T12:00:00"
)

# Function to get random element from array
get_random_element() {
    local array=("$@")
    echo "${array[$RANDOM % ${#array[@]}]}"
}

# Calculate commits per day (approximately equal distribution)
total_files=${#changed_files[@]}
files_per_day=$((total_files / ${#dates[@]}))
remainder=$((total_files % ${#dates[@]}))

echo "Distributing $total_files files across ${#dates[@]} days"
echo "Base files per day: $files_per_day, with $remainder extra files for some days"

# Distribute files to dates
file_index=0
for date_index in $(seq 0 $((${#dates[@]}-1))); do
    current_date=${dates[$date_index]}
    
    # Calculate how many files to commit on this day
    files_today=$files_per_day
    if [ $remainder -gt 0 ]; then
        files_today=$((files_today + 1))
        remainder=$((remainder - 1))
    fi
    
    echo "Day $(date -d "$current_date" +"%Y-%m-%d"): $files_today commits"
    
    # Process files for this day
    for i in $(seq 1 $files_today); do
        if [ $file_index -ge ${#changed_files[@]} ]; then
            echo "All files processed"
            exit 0
        fi
        
        file=${changed_files[$file_index]}
        
        # Create commit with random message
        prefix=$(get_random_element "${commit_prefixes[@]}")
        suffix=$(get_random_element "${commit_suffixes[@]}")
        commit_msg="$prefix $(basename "$file") $suffix"
        
        # Set the Git environment variables for date
        export GIT_AUTHOR_DATE="$current_date"
        export GIT_COMMITTER_DATE="$current_date"
        
        # Random offset hours and minutes to make commits look more natural
        hour_offset=$((RANDOM % 8 + 9))  # 9 AM to 5 PM
        minute_offset=$((RANDOM % 60))
        GIT_AUTHOR_DATE=$(date -d "$current_date $hour_offset hours $minute_offset minutes" +"%Y-%m-%dT%H:%M:%S")
        GIT_COMMITTER_DATE=$GIT_AUTHOR_DATE
        
        echo "Committing file ($((file_index+1))/${#changed_files[@]}): $file"
        echo "Date: $GIT_AUTHOR_DATE"
        echo "Message: $commit_msg"
        
        # Add and commit the file
        git add "$file"
        git commit -m "$commit_msg"
        
        # Push the commit
        git push origin HEAD
        
        file_index=$((file_index + 1))
        
        # Random sleep between commits (1-5 minutes) to simulate natural timing
        sleep_time=$((RANDOM % 300 + 60))
        echo "Waiting $sleep_time seconds before next commit..."
        sleep $sleep_time
    done
done

echo "All files have been committed and pushed successfully!"