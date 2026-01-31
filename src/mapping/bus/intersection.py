from tqdm import tqdm

def find_routes_passing_stops(bus):
    check_normal_bus = {}
    
    for key, values in tqdm(bus.items(), total=len(bus), desc='Intersecting paths', position=1, leave=False):
        times = [value[0] for value in values]
        roots = [value[1] for value in values]
        stops = [value[2] for value in values]
        types = [value[3] for value in values]
        
        results = []
        current_intersection = roots[0]
        previous_intersection = current_intersection
        temp_stops = [stops[0]]
        temp_times = [times[0]]
        intersection_count = 1      # 교집합이 유지된 횟수 카운트
        
        for root, time, stop in zip(roots[1::], times[1::], stops[1::]):
            if stop == temp_stops[-1]:  # 동일 정류장 연속 시
                continue

            current_intersection = set(current_intersection).intersection(root)
       
            if not current_intersection:    # 공집합
                if intersection_count > 2:
                    for (t, s) in zip(temp_times, temp_stops):
                        results.append([t, list(previous_intersection), s, '일반버스'])
                        
                # 교집합 초기화
                current_intersection = root
                previous_intersection = current_intersection
                temp_stops = [stop]
                temp_times = [time]
                intersection_count = 1
            else:
                previous_intersection = current_intersection
                temp_stops.append(stop)
                temp_times.append(time)
                intersection_count += 1
        
        if current_intersection and intersection_count > 2:
            for (t, s) in zip(temp_times, temp_stops):
                results.append([t, list(previous_intersection), s, '일반버스'])
        
        if results:        
            check_normal_bus[key] = results
        
    return check_normal_bus   