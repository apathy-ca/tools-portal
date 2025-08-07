#!/bin/bash

# DNS By Eye Generated Files Cleanup Script
# Cleans up old generated graph files to prevent disk space issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo -e "${BLUE}DNS By Eye Generated Files Cleanup${NC}"
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -d, --days DAYS     Delete files older than DAYS (default: 7)"
    echo "  -s, --size SIZE     Delete files if total size exceeds SIZE (e.g., 100M, 1G)"
    echo "  -f, --force         Skip confirmation prompt"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                  # Clean files older than 7 days"
    echo "  $0 -d 3             # Clean files older than 3 days"
    echo "  $0 -s 500M          # Clean files if total size > 500MB"
    echo "  $0 -d 1 -f          # Clean files older than 1 day without confirmation"
    echo ""
    echo "This script cleans up generated graph files in app/static/generated/"
}

# Default values
DAYS=7
SIZE_LIMIT=""
FORCE=false
GENERATED_DIR="app/static/generated"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--days)
            DAYS="$2"
            shift 2
            ;;
        -s|--size)
            SIZE_LIMIT="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

echo -e "${GREEN}DNS By Eye Generated Files Cleanup${NC}"
echo "=================================="

# Check if generated directory exists
if [ ! -d "$GENERATED_DIR" ]; then
    echo -e "${YELLOW}Generated files directory not found: $GENERATED_DIR${NC}"
    echo "Nothing to clean up."
    exit 0
fi

# Count current files
TOTAL_FILES=$(find "$GENERATED_DIR" -name "*.png" -type f | wc -l)
if [ "$TOTAL_FILES" -eq 0 ]; then
    echo -e "${YELLOW}No generated files found in $GENERATED_DIR${NC}"
    exit 0
fi

# Calculate current total size
TOTAL_SIZE=$(du -sh "$GENERATED_DIR" 2>/dev/null | cut -f1)
echo -e "${BLUE}Current status:${NC}"
echo "  Directory: $GENERATED_DIR"
echo "  Total files: $TOTAL_FILES"
echo "  Total size: $TOTAL_SIZE"
echo ""

# Find files to delete based on age
if [ -n "$DAYS" ]; then
    echo -e "${BLUE}Finding files older than $DAYS days...${NC}"
    OLD_FILES=$(find "$GENERATED_DIR" -name "*.png" -type f -mtime +$DAYS)
    OLD_COUNT=$(echo "$OLD_FILES" | grep -c . || echo "0")
    
    if [ "$OLD_COUNT" -gt 0 ]; then
        echo -e "${YELLOW}Found $OLD_COUNT files older than $DAYS days${NC}"
        if [ "$FORCE" = false ]; then
            echo "Files to be deleted:"
            echo "$OLD_FILES" | head -10
            if [ "$OLD_COUNT" -gt 10 ]; then
                echo "... and $((OLD_COUNT - 10)) more files"
            fi
            echo ""
            read -p "Delete these files? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Cleanup cancelled."
                exit 0
            fi
        fi
        
        echo -e "${BLUE}Deleting old files...${NC}"
        echo "$OLD_FILES" | xargs rm -f
        echo -e "${GREEN}✓ Deleted $OLD_COUNT old files${NC}"
    else
        echo -e "${GREEN}✓ No files older than $DAYS days found${NC}"
    fi
fi

# Check size limit if specified
if [ -n "$SIZE_LIMIT" ]; then
    echo -e "${BLUE}Checking size limit: $SIZE_LIMIT${NC}"
    
    # Convert size limit to bytes for comparison
    SIZE_BYTES=$(du -sb "$GENERATED_DIR" | cut -f1)
    LIMIT_BYTES=$(echo "$SIZE_LIMIT" | sed 's/[^0-9]*//g')
    
    # Convert units (rough approximation)
    if [[ "$SIZE_LIMIT" =~ [Gg] ]]; then
        LIMIT_BYTES=$((LIMIT_BYTES * 1024 * 1024 * 1024))
    elif [[ "$SIZE_LIMIT" =~ [Mm] ]]; then
        LIMIT_BYTES=$((LIMIT_BYTES * 1024 * 1024))
    elif [[ "$SIZE_LIMIT" =~ [Kk] ]]; then
        LIMIT_BYTES=$((LIMIT_BYTES * 1024))
    fi
    
    if [ "$SIZE_BYTES" -gt "$LIMIT_BYTES" ]; then
        echo -e "${YELLOW}Directory size ($TOTAL_SIZE) exceeds limit ($SIZE_LIMIT)${NC}"
        
        # Delete oldest files until under limit
        OLDEST_FILES=$(find "$GENERATED_DIR" -name "*.png" -type f -printf '%T@ %p\n' | sort -n | cut -d' ' -f2-)
        
        if [ "$FORCE" = false ]; then
            read -p "Delete oldest files to get under size limit? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Cleanup cancelled."
                exit 0
            fi
        fi
        
        echo -e "${BLUE}Deleting oldest files to reduce size...${NC}"
        DELETED_COUNT=0
        for file in $OLDEST_FILES; do
            rm -f "$file"
            DELETED_COUNT=$((DELETED_COUNT + 1))
            
            # Check size again
            NEW_SIZE_BYTES=$(du -sb "$GENERATED_DIR" 2>/dev/null | cut -f1 || echo "0")
            if [ "$NEW_SIZE_BYTES" -le "$LIMIT_BYTES" ]; then
                break
            fi
        done
        
        echo -e "${GREEN}✓ Deleted $DELETED_COUNT files to meet size limit${NC}"
    else
        echo -e "${GREEN}✓ Directory size is within limit${NC}"
    fi
fi

# Show final status
FINAL_FILES=$(find "$GENERATED_DIR" -name "*.png" -type f | wc -l)
FINAL_SIZE=$(du -sh "$GENERATED_DIR" 2>/dev/null | cut -f1)

echo ""
echo -e "${GREEN}Cleanup complete!${NC}"
echo -e "${BLUE}Final status:${NC}"
echo "  Files remaining: $FINAL_FILES"
echo "  Total size: $FINAL_SIZE"

if [ "$FINAL_FILES" -lt "$TOTAL_FILES" ]; then
    CLEANED_FILES=$((TOTAL_FILES - FINAL_FILES))
    echo -e "${GREEN}✓ Cleaned up $CLEANED_FILES files${NC}"
fi
