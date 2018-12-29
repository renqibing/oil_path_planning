import json
import sys

file_path = 'nimei.json'

def readJson(path):
    file = open(path)
    dataset = json.load(file)
    canvas_width = dataset['Canve_size_width']/10
    canvas_height = dataset['Canve_size_height']/10
    shape = dataset['Shape']
    polygons = []
    xyList = []
    for index,polygon in enumerate(shape):
        color = polygon['index']
        # color = index
        for poly in polygon['polygon']:
            xyList.append((float(poly['x'])/10,float(poly['y'])/10))
        # print(xyList)
        polygons.append([xyList,color])
        xyList = []
    return canvas_height,canvas_width,polygons


class canvas:
    def __init__(self,height,width):
        self.height = height
        self.width = width


class polygon:
    DEFAULT_COLOR = 'color_index'
    DEFAULT_COLOR_INDEX = '1'
    DEFAULT_PEN = 'pen_index'
    DEFAULT_PEN_INDEX = '1'

    def __init__(self,color_index,pen_index = 1):
        self.edge_properties = {}
        self.node_attr = {}
        self.node_neighbors = {}
        self.poly_attr = {'color_index':color_index,'pen_index':pen_index}

    def set_edge_properties(self,edge,**properties):
        self.edge_properties.setdefault(edge,{}).update(properties)
        if(edge[0]!=edge[1]):
            self.edge_properties.setdefault((edge[1],edge[0]),{}).update(properties)

    def add_node(self,node,attr):
        self.node_attr[node] = attr
        self.node_neighbors[node] = []

    def add_edge(self,u,v,wt = 1):
        if (u not in self.node_neighbors[v] and v not in self.node_neighbors[u]):
            self.node_neighbors[v].append(u)
            if(u != v):
                self.node_neighbors[u].append(v)
            self.set_edge_properties((u,v),weight = wt)

    def get_pen_attr(self):
        return self.poly_attr.setdefault(self.DEFAULT_PEN,self.DEFAULT_PEN_INDEX)

    def get_poly_attr(self):
        return self.poly_attr

    def __getitem__(self, node):
        for n in self.node_neighbors[node]:
            yield n

    def sort_nodes(self):
        return sorted(self.node_attr.items(),key= lambda d:d[1][1],reverse= True) # sort key in decreasing order of y

    def intersection(self,edge,height):
        u_x = self.node_attr[edge[0]][0]
        u_y = self.node_attr[edge[0]][1]
        v_x = self.node_attr[edge[1]][0]
        v_y = self.node_attr[edge[1]][1]
        if((height - u_y)*(height - v_y)>0):
            return None,None
        else:
            if(u_y == v_y):
                return (u_x,height),0
            else:
                x = (height-u_y)*(u_x-v_x)/float(u_y-v_y)+u_x
                x_ = round(x,5)
                height_ = round(height,5)
                inter_angle = float(u_y-v_y)/(u_x-v_x) if u_x != v_x else float(u_y-v_y)/(u_x-v_x+0.001)
                # print(inter_angle)
                return (x_,height_),inter_angle

# return a flag that adjust the height or the width of the stroke
    def check_intersection(self,temp,height,flag):
        # begin checking the nodes stored
        interpoint_set =[]
        stroke_size = 1
        i = 0
        while i < len(temp):
            node = temp[i]
            edges = ((node[0], v) for v in self.node_neighbors[node[0]])
            edges_ = list(edges)
            # print(edges_)
            # print(height)
            interpoint1,inter_angle1 = self.intersection(edges_[0], height)
            interpoint2,inter_angle2 = self.intersection(edges_[1], height)
            if (interpoint1 == None and interpoint2 == None):
                temp.remove(node)
                i -= 1
            else:
                if (interpoint2 != None):
                    interpoint_set.append(interpoint2)
                    if(abs(inter_angle2) < 1 and inter_angle2 !=0):
                        stroke_size = 2
                if (interpoint1 != None):
                    interpoint_set.append(interpoint1)
                    if( abs(inter_angle1) < 1 and inter_angle1 !=0):
                        stroke_size = 2
            i += 1

        if (flag == 1):
            interpoint_set_ = sorted(interpoint_set,key= lambda s:s[0])
        else:
            interpoint_set_ = sorted(interpoint_set,key= lambda s:s[0],reverse= True)
        lines = []

        for i in range(len(interpoint_set_)):
            # print(interpoint_set_[i])
            if i %2 == 0:
                templine = [interpoint_set_[i]]
            else:
                templine.append(interpoint_set_[i])
                lines.append(templine)
                templine = []
        # print(interpoint_set_)
        return lines,stroke_size

    def path_planning(self, width ): # width means width of stroke
        nodes = self.sort_nodes()
        width_ = width
        # search from the highest node
        height = nodes[0][1][1] - width_/2
        # store nodes temporarily when searching
        temp = []
        # store points of intersection temporarily
        interpoint_set = []
        # store series of paths
        paths = []
        # initial location
        location = 0
        # flag that reveals the last path
        flag = 0
        # number of searches
        search_num = 0
        stroke_size = 1
        # begin searching
        while(height > nodes[-1][1][1] and flag < 2):
            search_num += 1
            for i in range(location,len(nodes)):
                node = nodes[i]
                if(node[1][1] >= height):
                    temp.append(node)
                else:
                    interpoint_set,stroke_size = self.check_intersection(temp,height,search_num%2)
                    # update the step width
                    if (stroke_size == 2 and width_ == width): # only update the stroke size when it is original size
                        width_ = width/2
                        # print('using smaller stroke size')
                    elif(stroke_size == 1):
                        width_ = width
                    # print('intersection set is ',interpoint_set)
                    paths.append(interpoint_set)
                    location = i
                    height -= width_
                    # print('width ',width_)
                    if(height <= nodes[-1][1][1]):
                        height = nodes[-1][1][1] + width_/2
                        flag += 1
                    break
        return paths


if __name__ == '__main__':
    # inputfile = sys.argv[1]
    # outputfile = sys.argv[2]
    # width_ = sys.argv[3] if sys.argv[3] != None else 0.5
    # flag = sys.argv[4]

    inputfile = 'mulit-intersection.json'
    outputfile = 'test.json'
    width_ = 1
    flag = 0

    height,width,polygons = readJson(inputfile)
    mycanvas = canvas(height= height,width= width)
    polygon_ = {}
    path = []
    outline = []
    for item,block in enumerate(polygons):
        # print(block)
        mypolygon = polygon(color_index=block[-1])
        # print(block[0])
        for index, line in enumerate(block[0], start= 1):
            # print(index,line)
            if(flag):
                if (index != len(block[0])):
                    part_outline = [block[0][index-1], block[0][index]]
                else:
                    part_outline = [block[0][index-1],block[0][0]]
                outline.append(part_outline)

            mypolygon.add_node(node= index,attr= line)
            if(index>1):
                mypolygon.add_edge(u=index - 1, v=index)
                if(index == len(block[0])):
                    mypolygon.add_edge(u=index, v=1)
        lines = mypolygon.path_planning(float(width_))# width means the width of the strokes
        # print('lines',lines)
        if(flag):
            # lines.append(outline)
            outline_ = {'outline':outline}
            polygon_.update(outline_)
            outline = []
        lines_ = {'line':lines}
        polygon_.update(lines_)
        polygon_.update(mypolygon.get_poly_attr())
        polygon_.setdefault('index',item)
        # print(polygon_)
        path.append(polygon_)
        polygon_ = {}

    path_ = {'path':path}
    outputJson = {}
    outputJson.setdefault('canve_size_width',width)
    outputJson.setdefault('canve_size_height',height)
    outputJson.update(path_)
    outputJson.setdefault('outlines',flag)
    # print(outputJson)
    jf = open(outputfile,'w')
    jf.write(json.dumps(outputJson))
