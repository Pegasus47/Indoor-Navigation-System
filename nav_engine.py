import math

class NavigationEngine:
    def __init__(self, snapping_threshold=1.0):
        self.nodes = {}  # { "Node_Name": (x, y, z) }
        self.graph = {}  # { "Node_Name": { "Neighbor_Name": distance } }
        self.threshold = snapping_threshold

    def build_graph(self, entities_by_layer):
        """Processes waypoints and track lines into a graph."""
        self.nodes.clear()
        self.graph.clear()

        # 1. Extract Waypoints (Nodes)
        waypoint_layer = 'Defpoints' 
        for entity in entities_by_layer.get(waypoint_layer, []):
            if entity.dxftype() == 'INSERT':
                name = self._get_node_name(entity)
                pos = entity.dxf.insert # (x, y, z)
                self.nodes[name] = pos
                self.graph[name] = {}

        # 2. Extract Track Lines (Edges)
        path_layer = 'trackline'
        for entity in entities_by_layer.get(path_layer, []):
            if entity.dxftype() == 'LINE':
                start_pt = entity.dxf.start
                end_pt = entity.dxf.end
                
                # Find which waypoints these coordinates 'snap' to
                u = self._find_closest_node(start_pt)
                v = self._find_closest_node(end_pt)

                if u and v and u != v:
                    dist = self._calculate_distance(self.nodes[u], self.nodes[v])
                    self.graph[u][v] = dist
                    self.graph[v][u] = dist # Bi-directional walking path

        print(f"Graph Built: {len(self.nodes)} nodes, {sum(len(v) for v in self.graph.values())//2} edges")
        
        for start_pt,coords in self.nodes.items(): #.items() iterates key,value ,else only key is iterated over 
            for node,adj_list in self.graph.items():
                if(start_pt==node):
                    print(f"{start_pt}:{coords}")
                    print("---------------------")
                    for end_pt,dist in adj_list.items():
                        print(f"{start_pt}---{dist:.2f}---{end_pt}") 

    def _get_node_name(self, entity):
        for attrib in entity.attribs:
            if attrib.dxf.tag in ['ID', 'NAME']:
                return attrib.dxf.text
        return f"Node_{id(entity)}"

    def _find_closest_node(self, point):
        best_node = None
        min_dist = self.threshold
        for name, pos in self.nodes.items():
            d = self._calculate_distance(point, pos)
            if d < min_dist:
                min_dist = d
                best_node = name
        return best_node

    def _calculate_distance(self, p1, p2):
        # 3D Distance Formula: sqrt((x2-x1)^2 + (y2-y1)^2 + (z2-z1)^2)
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))