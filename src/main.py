from logger import logger
import config
import graphql
from datetime import datetime

def release_based_on_duedate():
    if config.is_enterprise:
        issues = graphql.get_project_issues(
            owner=config.repository_owner,
            owner_type=config.repository_owner_type,
            project_number=config.project_number,
            duedate_field_name=config.duedate_field_name,
            filters={'open_only': True}
        )
    else:
        issues = graphql.get_repo_issues(
            owner=config.repository_owner,
            repository=config.repository_name,
            duedate_field_name=config.duedate_field_name
        )

    if not issues:
        logger.info('No issues have been found')
        return

    #-------------------------------------------
    # Get the project_id, release_field_id 
    #-------------------------------------------

    project_title = 'Test'
    
    project_id = graphql.get_project_id_by_title(
        owner=config.repository_owner, 
        project_title=project_title
    )

    # logger.info(f'Printing the project_id: {project_id}')

    if not project_id:
        logging.error(f"Project {project_title} not found.")
        return None
    
    release_field_id = graphql.get_release_field_id(
        project_id=project_id,
        release_field_name=config.release_field_name
    )

    # logger.info(f"Printing the release_field_id: {release_field_id}")

    if not release_field_id:
        logging.error(f"Release field not found in project {project_title}")
        return None

    #-------------------------------------------------------------------------
    
    release_options = graphql.get_release_field_options(project_id)
    if not release_options:
        logger.error("Failed to fetch release options.")
        return

    for project_item in issues:

        # Skip the closed issues
        if issue.get('state') == 'CLOSED':
            continue
            
        issue = project_item.get('content')
        if not issue:
            logger.error(f"Missing 'content' in project item: {project_item}")
            continue

        due_date = project_item.get('fieldValueByName', {}).get(config.duedate_field_name)
        if not due_date:
            logger.info(f"No due date for issue {issue.get('title')}. Skipping.")
            continue

        # Parse and compare the due date
        try:
            due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
            release_to_update = find_matching_release(release_options, due_date_obj)

            if release_to_update:
                logger.info(f"Due date for issue {issue.get('title')} is {due_date_obj}. Changing release...")
                
            # Update the release field for the issue
            updated = graphql.update_issue_release(
                owner=config.repository_owner,
                project_title=project_title,
                project_id=project_id,
                release_field_id=release_field_id,
                item_id=item_id,
                release_option_id=release_option_id
            )
            if updated:
                logger.info(f"Successfully updated issue {issue.get('id')} to the release option.")
            else:
                logger.error(f"Failed to update issue {issue.get('id')}.")
    except (ValueError, TypeError):
        continue

# Find the correct release based on the due date
def find_matching_release(release_options, due_date):
    for release_name, release_data in release_options.items():
        if release_data['start_date'] <= due_date <= release_data['end_date']:
            return release_data
    return None

def main():
    logger.info('Process started...')
    if config.dry_run:
        logger.info('DRY RUN MODE ON!')

    # Notify about due date changes and release updates
   release_based_on_duedate()

if __name__ == "__main__":
    main()
