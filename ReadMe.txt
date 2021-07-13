Run simulation file: Base_RTO (Jupyter notebook file)

Just need to input dates and hours (start time and and time) and the simulation runs
based on the base RTO algorithm (assigns incoming rider to shuttle based on 
minimizing marginal costs). 

Other python files:
BASECASE_RouteRiderVanClass: Defines classes for shuttles and riders
BASECASE_RouteSimClass: Defines the simulation environment

Data files:
3e_medTravTimes.csv - processed shuttle trajectory data to compute time dependent travel times
28x_Arrival_Times.csv - outbound 28x bus schedule (mainline transit)
28x_Departure_Times.csv - inbound 28x bus schedlue (for transfer coordination)
riderData_07_15_19 - One day of ridership data
requestsDict - dictionary of all request unique IDs for each date

