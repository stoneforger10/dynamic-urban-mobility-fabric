# Interaction sketch

```powershell
genlayer write ADDRESS create_network --args 'city-demo','Demo City'
genlayer write ADDRESS add_node --args 'city-demo','zone-a','ZONE',1000
genlayer write ADDRESS add_node --args 'city-demo','hub-a','HUB',5000
genlayer write ADDRESS propose_change --args 'city-demo','edge-1',0,'ADD_CONNECTION','edge-1','zone-a','hub-a','BUS',DEADLINE
genlayer write ADDRESS apply_change --args 'city-demo','edge-1'
genlayer call ADDRESS get_network --args 'city-demo'
```
