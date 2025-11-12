from typing import List, Optional
from django.db import transaction
from django.contrib.auth import get_user_model

from content.models import (
    Exploration, ExplorationState, Hint, AnswerGroup, RuleSpec, Solution,
    InteractionCustomizationArg
)
from content.domains.exploration_domain import (
    ExplorationDomain, ExplorationStateDomain, ExplorationTransitionDomain
)
from content.domains.commands import (
    CreateExplorationCommand, UpdateExplorationCommand, PublishExplorationCommand,
    AddExplorationStateCommand, UpdateExplorationStateCommand, AddExplorationTransitionCommand
)


User = get_user_model()


class ExplorationService:
    """Service for managing explorations (interactive lessons)."""

    @transaction.atomic
    def create_exploration(self, input_data: CreateExplorationCommand) -> ExplorationDomain:
        input_data.validate()
        owner = User.objects.filter(id=input_data.owner_id).first()
        exploration = Exploration.objects.create(
            title=input_data.title,
            owner=owner,
            language=input_data.language
        )
        return ExplorationDomain.from_model(exploration)

    def list_explorations(self) -> List[ExplorationDomain]:
        return [ExplorationDomain.from_model(e) for e in Exploration.objects.all()]

    @transaction.atomic
    def update_exploration(self, exploration_id: str, update_data: UpdateExplorationCommand) -> Optional[ExplorationDomain]:
        try:
            exp = Exploration.objects.get(id=exploration_id)
        except Exploration.DoesNotExist:
            return None
        update_data.validate()
        if update_data.title: exp.title = update_data.title
        if update_data.language: exp.language = update_data.language
        exp.save()
        return ExplorationDomain.from_model(exp)

    @transaction.atomic
    def publish_exploration(self, exploration_id: str, publish_data: PublishExplorationCommand) -> Optional[ExplorationDomain]:
        try:
            exp = Exploration.objects.get(id=exploration_id)
        except Exploration.DoesNotExist:
            return None
        publish_data.validate()
        exp.published = publish_data.published
        exp.save()
        return ExplorationDomain.from_model(exp)

    @transaction.atomic
    def unpublish_exploration(self, exploration_id: str) -> Optional[ExplorationDomain]:
        try:
            exp = Exploration.objects.get(id=exploration_id)
        except Exploration.DoesNotExist:
            return None
        exp.published = False
        exp.save()
        return ExplorationDomain.from_model(exp)

    @transaction.atomic
    def update_exploration_from_json(self, exploration_id: str, full_data: dict) -> Optional[ExplorationDomain]:
        try:
            exploration = Exploration.objects.get(id=exploration_id)
        except Exploration.DoesNotExist:
            return None

        # 1. Update Exploration metadata
        exploration.title = full_data.get('title', exploration.title)
        exploration.objective = full_data.get('objective', exploration.objective)
        exploration.language = full_data.get('language', exploration.language)
        exploration.init_state_name = full_data.get('init_state_name', exploration.init_state_name)
        exploration.save()

        # 2. Diff and update states
        states_data = full_data.get('states', {})
        existing_states = {s.name: s for s in exploration.states.all()}
        received_state_names = set(states_data.keys())
        existing_state_names = set(existing_states.keys())

        # Delete states not in the new data
        states_to_delete = existing_state_names - received_state_names
        if states_to_delete:
            ExplorationState.objects.filter(exploration=exploration, name__in=states_to_delete).delete()

        # Create/Update states
        for state_name, state_data in states_data.items():
            state, created = ExplorationState.objects.update_or_create(
                exploration=exploration,
                name=state_name,
                defaults={
                    'content_html': state_data.get('content', {}).get('html'),
                    'interaction_id': state_data.get('interaction', {}).get('id'),
                    'card_is_checkpoint': state_data.get('card_is_checkpoint', False),
                }
            )

            # 3. Update state's nested objects
            interaction_data = state_data.get('interaction', {})
            
            # Hints
            state.hints.all().delete()
            for i, hint_data in enumerate(interaction_data.get('hints', [])):
                Hint.objects.create(state=state, hint_index=i, hint_html=hint_data.get('hint_content', {}).get('html'))

            # Answer Groups and their Rule Specs
            state.answer_groups.all().delete()
            for i, ag_data in enumerate(interaction_data.get('answer_groups', [])):
                ag = AnswerGroup.objects.create(
                    state=state,
                    group_index=i,
                    outcome_dest=ag_data.get('outcome', {}).get('dest'),
                    outcome_feedback_html=ag_data.get('outcome', {}).get('feedback', {}).get('html'),
                    labelled_as_correct=ag_data.get('outcome', {}).get('labelled_as_correct', False),
                    tagged_skill_misconception_id=ag_data.get('tagged_skill_misconception_id')
                )
                for j, rule_data in enumerate(ag_data.get('rule_specs', [])):
                    RuleSpec.objects.create(
                        answer_group=ag,
                        rule_index=j,
                        rule_type=rule_data.get('type'),
                        inputs_json=rule_data.get('inputs', {})
                    )
            
            # Solution
            solution_data = interaction_data.get('solution')
            if solution_data:
                Solution.objects.update_or_create(
                    state=state,
                    defaults={
                        'correct_answer': solution_data.get('correct_answer'),
                        'answer_is_exclusive': solution_data.get('answer_is_exclusive', False),
                        'solution_explanation_html': solution_data.get('explanation', {}).get('html')
                    }
                )
            else:
                Solution.objects.filter(state=state).delete()

            # Customization Args
            state.customization_args.all().delete()
            for arg_name, arg_value in interaction_data.get('customization_args', {}).items():
                InteractionCustomizationArg.objects.create(
                    state=state,
                    interaction_id=state.interaction_id,
                    arg_name=arg_name,
                    arg_value_json=arg_value
                )

        return self.get_exploration_details(exploration_id)

    def get_exploration_details(self, exploration_id: str) -> Optional[ExplorationDomain]:
        try:
            exploration = Exploration.objects.prefetch_related(
                'states__hints', 
                'states__answer_groups__rule_specs', 
                'states__solution',
                'states__customization_args',
                'category',
                'tags'
            ).get(id=exploration_id)
            return ExplorationDomain.from_model(exploration)
        except Exploration.DoesNotExist:
            return None


class ExplorationStateService:
    """Service for managing exploration states."""

    @transaction.atomic
    def create_state(self, input_data: AddExplorationStateCommand) -> ExplorationStateDomain:
        input_data.validate()
        exploration = Exploration.objects.get(id=input_data.exploration_id)
        state = ExplorationState.objects.create(
            exploration=exploration,
            name=input_data.name,
            content=input_data.content,
            interaction=input_data.interaction
        )
        return ExplorationStateDomain.from_model(state)

    def list_states(self, exploration_id: str) -> List[ExplorationStateDomain]:
        return [ExplorationStateDomain.from_model(s) for s in ExplorationState.objects.filter(exploration_id=exploration_id)]

    @transaction.atomic
    def update_state(self, state_id: str, update_data: UpdateExplorationStateCommand) -> Optional[ExplorationStateDomain]:
        try:
            state = ExplorationState.objects.get(id=state_id)
        except ExplorationState.DoesNotExist:
            return None
        update_data.validate()
        if update_data.name: state.name = update_data.name
        if update_data.content: state.content.update(update_data.content)
        if update_data.interaction: state.interaction.update(update_data.interaction)
        state.save()
        return ExplorationStateDomain.from_model(state)


class ExplorationTransitionService:
    """Service for managing exploration transitions."""

    @transaction.atomic
    def create_transition(self, input_data: AddExplorationTransitionCommand) -> ExplorationTransitionDomain:
        input_data.validate()
        exploration = Exploration.objects.get(id=input_data.exploration_id)
        from_state = ExplorationState.objects.get(exploration_id=input_data.exploration_id, name=input_data.from_state)
        to_state = ExplorationState.objects.get(exploration_id=input_data.exploration_id, name=input_data.to_state)
        transition = ExplorationTransition.objects.create(
            exploration=exploration,
            from_state=from_state,
            to_state=to_state,
            condition=input_data.condition
        )
        return ExplorationTransitionDomain.from_model(transition)

    def list_transitions(self, exploration_id: str) -> List[ExplorationTransitionDomain]:
        return [ExplorationTransitionDomain.from_model(t) for t in ExplorationTransition.objects.filter(exploration_id=exploration_id)]