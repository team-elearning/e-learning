from rest_framework import generics, permissions    
from rest_framework.response import Response
from rest_framework import status                                                                               

from content import models      
from content.serializers import ExplorationStateSerializer, AddExplorationStateInputSerializer                                     
from content.services.exploration_service import ExplorationStateService                                                           
from custom_account.api.permissions import IsOwnerOrAdmin                                                                          
                                                                                                                               
class ExplorationStateListCreateView(generics.ListCreateAPIView):                                                                  
    """                                                                                                                            
    GET /api/explorations/{exploration_id}/states/                                                                                 
    POST /api/explorations/{exploration_id}/states/                                                                                
    """                                                                                                                            
    serializer_class = ExplorationStateSerializer                                                                                  
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]                                                                   
                                                                                                                           
    def get_queryset(self):                                                                                                        
        exploration_id = self.kwargs.get("exploration_id")                                                                         
        return models.ExplorationState.objects.filter(exploration_id=exploration_id)                                               
                                                                                                                                
    def create(self, request, exploration_id=None, *args, **kwargs):                                                               
        serializer = AddExplorationStateInputSerializer(data=request.data)                                                         
        serializer.is_valid(raise_exception=True)                                                                                  
        cmd = serializer.to_domain(exploration_id=exploration_id)                                                                  
        created_domain = ExplorationStateService.create_state(cmd)                                                                 
        return Response(ExplorationStateSerializer.from_domain(created_domain), status=status.HTTP_201_CREATED)                    
                                                                                                                         
                                                                                                                              
class ExplorationStateDetailView(generics.RetrieveUpdateDestroyAPIView):                                                           
    queryset = models.ExplorationState.objects.all()                                                                               
    serializer_class = ExplorationStateSerializer                                                                                  
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]                                                   
                                                                                                                               
    def update(self, request, *args, **kwargs):                                                                                    
        instance = self.get_object()                                                                                               
        serializer = self.get_serializer(instance, data=request.data, partial=True)                                                
        serializer.is_valid(raise_exception=True)                                                                                  
        updates = serializer.validated_data                                                                                        
        updated_domain = exploration_state_service.update_state(state_id=instance.id, update_data=updates)                         
        if not updated_domain:                                                                                                     
            return Response({"detail": "Cannot update state"}, status=status.HTTP_400_BAD_REQUEST)                                 
        return Response(ExplorationStateSerializer.from_domain(updated_domain))  