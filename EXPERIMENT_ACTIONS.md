# Experiment Actions Documentation

## Overview

The ARCH-FL dashboard now supports comprehensive experiment management with individual and batch actions. This document describes all available actions, their constraints, and usage patterns.

## Available Actions

### Individual Experiment Actions

Each experiment can be controlled with the following actions based on its current status:

#### Run Action
- **Status**: Available for experiments with status `pending`
- **Icon**: 🟢 Play
- **Color**: Green
- **Function**: Starts experiment execution
- **Constraint**: Only one execution instance allowed per experiment

#### Cancel Action
- **Status**: Available for experiments with status `running` or `pending`
- **Icon**: 🟡 Stop
- **Color**: Yellow
- **Function**: Stops experiment execution
- **Constraint**: Cannot cancel already completed/cancelled experiments

#### Restart Action
- **Status**: Available for experiments with status `completed`, `cancelled`, or `failed`
- **Icon**: 🔄 Redo
- **Color**: Blue
- **Function**: Restarts experiment execution from beginning
- **Constraint**: Creates new execution instance

#### Delete Action
- **Status**: Available for experiments NOT in `running` status
- **Icon**: 🔴 Trash
- **Color**: Red
- **Function**: Permanently deletes experiment and all results
- **Constraint**: Cannot delete running experiments (must cancel first)

### Batch Actions

Multiple experiments can be selected and controlled simultaneously:

#### Select/Deselect
- **Select All**: Toggle button in header to select all visible experiments
- **Individual Selection**: Checkbox in each row
- **Deselect All**: Toggle button when all selected

#### Batch Action Menu
- **Trigger**: "Actions" button appears when experiments are selected
- **Shows**: Only actions valid for the selected group
- **Executes**: All valid actions on selected experiments
- **Reports**: Success/failure for each experiment

## Action Constraints

### Status-Based Constraints

| Status | Run | Cancel | Restart | Delete |
|--------|-----|--------|---------|-------|
| pending | ✅ | ✅ | ❌ | ✅ |
| running | ❌ | ✅ | ❌ | ❌ |
| completed | ❌ | ❌ | ✅ | ✅ |
| cancelled | ✅ | ❌ | ✅ | ✅ |
| failed | ✅ | ❌ | ✅ | ✅ |

### Execution Constraints

1. **Single Instance**: Each experiment can only execute once at a time
2. **Running Protection**: Cannot delete or modify running experiments
3. **Status Transitions**: 
   - pending → running → completed/failed/cancelled
   - cancelled/completed/failed → pending (via restart)

## API Endpoints

### Individual Actions

```bash
# Run experiment
POST /api/v1/experiments/{id}/run

# Cancel experiment
POST /api/v1/experiments/{id}/cancel

# Restart experiment
POST /api/v1/experiments/{id}/restart

# Delete experiment
POST /api/v1/experiments/{id}/delete
```

### Batch Actions

```bash
# Batch actions
POST /api/v1/experiments/actions
Content-Type: application/json

{
  "action": "run|cancel|restart|delete",
  "experiment_ids": [1, 2, 3]
}
```

## Response Format

### Success Response
```json
{
  "action": "run",
  "total_experiments": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "experiment_id": 1,
      "status": "success",
      "message": "Experiment execution started"
    }
  ],
  "errors": []
}
```

### Error Response
```json
{
  "action": "delete",
  "total_experiments": 2,
  "successful": 1,
  "failed": 1,
  "results": [
    {
      "experiment_id": 1,
      "status": "success",
      "message": "Experiment deleted successfully"
    }
  ],
  "errors": [
    {
      "experiment_id": 2,
      "status": "error",
      "message": "Cannot delete a running experiment. Please cancel it first."
    }
  ]
}
```

## Frontend Implementation

### Experiments List Page

#### Selection Features
- **Checkbox Column**: First column with checkbox for each experiment
- **Select All**: Header checkbox to select/deselect all visible experiments
- **Selection Counter**: Badge showing number of selected experiments
- **Action Button**: "Actions" button when experiments selected

#### Individual Action Buttons
- **Run**: Green button for pending experiments
- **Cancel**: Yellow button for running experiments
- **Restart**: Blue button for completed/cancelled/failed experiments
- **Delete**: Red button for non-running experiments

### Experiment Detail Page

#### Action Buttons
- **Status-Specific**: Only show relevant actions for current status
- **Loading State**: Disable buttons during action execution
- **Success Notification**: Show confirmation after action completes
- **Error Notification**: Show error message if action fails

## Usage Examples

### Starting an Experiment
```javascript
// Individual experiment
const response = await experimentService.run(experimentId)

// Batch action
const response = await experimentService.batchActions({
  action: 'run',
  experiment_ids: [1, 2, 3]
})
```

### Canceling Running Experiments
```javascript
// Individual experiment
const response = await experimentService.cancel(experimentId)

// Batch action - cancel all running experiments
const runningExperiments = experiments.filter(exp => exp.status === 'running')
const response = await experimentService.batchActions({
  action: 'cancel',
  experiment_ids: runningExperiments.map(exp => exp.id)
})
```

### Cleaning Up Completed Experiments
```javascript
// Delete multiple completed experiments
const completedExperiments = experiments.filter(exp => exp.status === 'completed')
const response = await experimentService.batchActions({
  action: 'delete',
  experiment_ids: completedExperiments.map(exp => exp.id)
})
```

### Restarting Failed Experiments
```javascript
// Restart failed experiments
const failedExperiments = experiments.filter(exp => exp.status === 'failed')
const response = await experimentService.batchActions({
  action: 'restart',
  experiment_ids: failedExperiments.map(exp => exp.id)
})
```

## Error Handling

### Common Errors

1. **Running Experiment Constraint**
   ```
   "Cannot delete a running experiment. Please cancel it first."
   ```

2. **Already Running**
   ```
   "Experiment is already running"
   ```

3. **Invalid Status for Action**
   ```
   "Only running or pending experiments can be cancelled"
   ```

4. **Experiment Not Found**
   ```
   "Experiment not found"
   ```

### Error Recovery

```javascript
try {
  const response = await experimentService.batchActions({
    action: 'delete',
    experiment_ids: [1, 2, 3]
  })
  
  if (response.errors.length > 0) {
    console.log(`Failed to delete ${response.errors.length} experiments`)
    response.errors.forEach(error => {
      console.log(`Experiment ${error.experiment_id}: ${error.message}`)
    })
  }
  
} catch (error) {
  console.error('Batch action failed:', error)
}
```

## Best Practices

### Batch Operations
1. **Validate Before Execution**: Check constraints before batch actions
2. **Handle Partial Failures**: Expect some experiments to fail
3. **Provide Feedback**: Show success/failure details to users
4. **Refresh Data**: Update UI after batch operations

### Individual Operations
1. **Disable During Execution**: Prevent duplicate actions
2. **Show Loading State**: Indicate operation in progress
3. **Confirm Destructive Actions**: Warn before delete operations
4. **Provide Confirmation**: Show success/error notifications

### Status Management
1. **Poll for Updates**: Check status after starting experiments
2. **Handle Transitions**: Update UI when status changes
3. **Prevent Conflicts**: Disable conflicting actions
4. **Show Progress**: Indicate execution status

## UI/UX Guidelines

### Visual Design
- **Color Coding**: Use consistent colors for each action type
- **Icon Consistency**: Use standard icons for each action
- **Loading States**: Show loading indicators during operations
- **Disabled States**: Gray out unavailable actions

### Interaction Patterns
- **Hover States**: Highlight buttons on hover
- **Focus States**: Ensure keyboard navigation works
- **Feedback**: Provide immediate visual feedback
- **Accessibility**: Support keyboard and screen reader users

### Notification Patterns
- **Success**: Green notification with checkmark
- **Error**: Red notification with error message
- **Dismissible**: Allow users to dismiss notifications
- **Persistent**: Keep important errors visible

## Testing Strategy

### Unit Tests
- **Action Validation**: Test status-based action availability
- **Constraint Enforcement**: Verify constraints are enforced
- **Error Handling**: Test error responses
- **API Calls**: Mock API calls and test responses

### Integration Tests
- **End-to-End**: Test complete action workflows
- **Batch Operations**: Test multi-experiment actions
- **Status Transitions**: Verify status changes
- **Error Recovery**: Test error handling and recovery

### System Tests
- **Concurrency**: Test multiple simultaneous actions
- **Performance**: Measure action execution times
- **Scalability**: Test with large numbers of experiments
- **Reliability**: Test under various conditions

## Future Enhancements

### Planned Features
1. **Pause/Resume**: Add pause capability for long-running experiments
2. **Priority Scheduling**: Allow prioritizing certain experiments
3. **Dependency Management**: Support experiment dependencies
4. **Resource Limits**: Add resource allocation controls
5. **Scheduling**: Schedule experiments for future execution

### Advanced Features
1. **Conditional Actions**: Actions based on experiment properties
2. **Bulk Configuration**: Apply settings to multiple experiments
3. **Template Actions**: Save and reuse action sequences
4. **Audit Logging**: Track all experiment actions
5. **Rollback**: Undo experiment changes

## Summary

The experiment action system provides comprehensive control over experiment lifecycle with:

- **Individual Actions**: Fine-grained control per experiment
- **Batch Actions**: Efficient management of multiple experiments
- **Constraint Enforcement**: Prevent invalid operations
- **Error Handling**: Graceful handling of errors
- **User Feedback**: Clear notifications and status updates

This system enables efficient experiment management while maintaining data integrity and preventing invalid operations.
