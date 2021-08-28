#!/bin/bash

stack_name="Tweeter"

export BUILD_DIR=build
export CLOUD_ID="goudham"

template_path=${BUILD_DIR}/${stack_name}.json
change_set_name=${CLOUD_ID}-$(date -u "+%Y-%m-%dT%H-%M-%SZ")

change_set_params="--change-set-name $change_set_name"
stack_params="--stack-name $stack_name"
create_params="$stack_params \
--template-body file://$template_path \
--capabilities CAPABILITY_IAM"

create_change_set_params="$change_set_params $create_params"

stack_status="$(aws cloudformation list-stacks \
| jq '.StackSummaries[]|
select(.StackName == "'${stack_name}'"
and .StackStatus != "DELETE_COMPLETE")|
.StackStatus' | \
tr -d '"')"

if [[ "$stack_status" =~ "FAILED" ]] || [[ "$stack_status" =~ "IN_PROGRESS" ]] || [[ "$stack_status" == "ROLLBACK_COMPLETE" ]]; then
    echo "ERROR: $stack_name is in a $stack_status state, exiting..."
    exit 1
fi

#Build the template
make STACK_NAME=${stack_name}
source stacks-venv/Scripts/activate

if [[ "$stack_status" == "" ]] || [[ " DELETE_COMPLETE ROLLBACK_COMPLETE " =~ " $stack_status " ]]; then
    # CREATE
    aws cloudformation create-stack ${create_params} --capabilities CAPABILITY_IAM
    aws cloudformation wait stack-create-complete ${stack_params} &> /dev/null
    if [[ "$?" -ne "0" ]]; then
        echo "ERROR: Failed to create $stack_name"
        exit 1
    fi
else
    # UPDATE
    change_sets="$(aws cloudformation list-change-sets ${stack_params})"
    change_set_count="$(echo ${change_sets} | jq '.Summaries|length')"
    if [[ "$change_set_count" -gt "0" ]]; then
        echo "ERROR: $stack_name has $change_set_count outstanding change sets, please execute or delete them."
        exit 1
    fi

    create_change_set_response=$(aws cloudformation create-change-set ${create_change_set_params})
    change_set_arn="$(echo ${create_change_set_response} | jq '.Id' | tr -d '"')"
    echo "Creating change set $change_set_name for stack $stack_name"

    aws cloudformation wait change-set-create-complete ${change_set_params} ${stack_params} &> /dev/null

    # Most likely failed because there are no changes to apply.
    if [[ "$?" -ne "0" ]]; then
        echo "No changes to apply, exiting"
        aws cloudformation delete-change-set --change-set-name=${change_set_arn} &> /dev/null
        exit 0
    fi

    echo "Change set $change_set_name created for stack $stack_name"

    stack_template=$(aws cloudformation get-template --stack-name ${stack_name} | jq -S .)
    change_set_template=$(aws cloudformation get-template --change-set-name "${change_set_name}" --stack-name ${stack_name} | jq -S .)
    template_diff=$(diff -u <(echo "${stack_template}") <(echo "${change_set_template}") | ydiff -w 0 -s --color=always)

    echo "Changes to be applied:"

    if [[ "$(echo "${template_diff}" | wc -l)" -gt 1 ]]; then
        echo "${template_diff}"
    fi

    echo "Are you happy with your changes? (yes/no)"
    read -r input
    if [ "$input" == "no" ]; then
        echo "Exiting..."
        exit 1
    fi

    echo "Applying changes..."

    aws cloudformation execute-change-set --change-set-name ${change_set_arn}
    aws cloudformation wait stack-update-complete ${stack_params}

    if [[ "$?" -ne "0" ]]; then
        echo "ERROR: Failed to update $stack_name with change set $change_set_name"
        exit 1
    fi
fi

echo "Successfully applied change set $change_set_name to stack $stack_name"