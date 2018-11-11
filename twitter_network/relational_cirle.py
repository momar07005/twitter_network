# coding: utf-8

# # Visualizing Twitter Community Graph Network with Plotly
#
# In the first script in this repo, I gathered the Tweets, usernames, and friends of a community that participated in a Twitter chat. This script can be used to visualize the network with Plotly.

import plotly.plotly as py
import plotly
from plotly.graph_objs import *
import networkx as nx
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# get_ipython().run_line_magic('matplotlib', 'inline')
import math
import community


# import sys
# get_ipython().system('{sys.executable} -m pip install python-louvain')


# The CSV in question has 4 columns, a list of usernames that the friendship originates from, a list of user IDs that the friendship originates from, a list of usernames that the friendship points to, and a list of user IDs that the friendship points to. We will name the nodes with the user IDs and user the usernames as a characteristic of the nodes.

# In[366]:
# 'test_data.csv'
def analyse(csv_file, width, height):
    df = pd.read_csv(csv_file)

    # In[580]:

    # Convert user ID from float to integer.
    df.userFromId = df.userFromId.apply(lambda x: int(x))
    df.userToId = df.userToId.apply(lambda x: int(x))

    # This is a directed graph since Twitter relationships are not necessarily reciprocal. Although Plotly does not offer a simple way to visualize this insofar that I am aware unlike Gephi, contructing the graph in this way will allow for easier display later of followers, following, etc.

    # In[581]:

    G = nx.Graph()
    for lab, row in df.iterrows():
        G.add_edge(int(row['userFromId']), int(row['userToId']), weight=int(row['weight']))

    # In[582]:

    temp = zip(df['userFromId'], df['userToId'])

    # In[583]:

    # Give nodes their Usernames
    dfLookup = df[['userFromName', 'userFromId', 'userToName', 'userToId']].drop_duplicates()
    users = [{'userName': row['userFromName'], 'userId': row['userFromId']} for lab, row in dfLookup.iterrows()]
    [users.append({'userName': row['userToName'], 'userId': row['userToId']}) for lab, row in dfLookup.iterrows()]

    # In[584]:

    for user in users:
        G.node[user['userId']]['userName'] = user['userName']

    # ## Configure Position
    # The cell that follows is only to experiment with possible node positioning. The NetworkX Spring Layout positioning can be manipulated somewhat with the "k=" and "iterations=" parameters.

    # ## Define Positioning
    #
    # Plotly does not have a true library for graph theory. We will use NetworkX to define the position of coordinates of a scatterplot and the attributes to describe the nodes of that scatterplot. Once a positioning is determined above, define it below as "pos", a dictionary of x and y coordinates.

    pos = nx.spring_layout(G, k=.12, dim=3)

    # Plotly allows for display of any measures calculated. Some possible measures include indegree (followers), outdegree (following) and centrality.

    betweenessCentralScore = nx.betweenness_centrality(G, weight='weight')
    degreeCentralScore = nx.degree_centrality(G)
    pageRankScore = nx.pagerank(G)

    # Creating a list of pagerank, betweenness centrality, degree centrality
    # of all the characters in the fifth book.
    measures = [betweenessCentralScore,
                degreeCentralScore,
                pageRankScore]

    # Creating the correlation DataFrame
    cor = pd.DataFrame.from_records(measures)

    # Calculating the correlation
    correlations = cor.T.corr()
    b_cent_most_important, d_cent_most_important, p_rank_most_important = cor.idxmax(axis=1)

    # ## Define scatter_nodes() and scatter_edges()
    #
    # These functions create Plotly "traces" of the nodes and edges using the layout defined in "pos". Here, I have chosen to color the nodes by the betweenness centrality, but one might choose to vary size of the nodes instead, or vary by another characteristic such as degree.

    # Get a list of all nodeID in ascending order
    nodeID = G.node.keys()
    nodeID = sorted(nodeID)

    # Node label information available on hover. Note that some html tags such as line break <br> are recognized within a string.
    labels = []

    for nd in nodeID:
        user_name = G.node[nd]['userName']
        # Here you are going to change the url and add a parameter username [GET]
        label =  "<a href='#'> "+ user_name +"</a>"
        labels.append(label)

    # ## Configure the plot and call Plotly
    width = width
    height = height
    axis = dict(showline=False,  # hide axis line, grid, ticklabels and  title
                zeroline=False,
                showgrid=False,
                showticklabels=False,
                title=''
                )
    layout = Layout(title='Community on Twitter',
                    font=Font(),
                    showlegend=False,
                    autosize=False,
                    width=width,
                    height=height,
                    scene=dict(
                        xaxis=dict(axis),
                        yaxis=dict(axis),
                        zaxis=dict(axis),
                    ),
                    margin=Margin(
                        l=40,
                        r=40,
                        b=85,
                        t=100,
                        pad=0,

                    ),
                    hovermode='closest',
                    plot_bgcolor='#EFECEA',  # set background color
                    )

    partition = community.best_partition(G)
    modularity = community.modularity(partition, G)

    # In[742]:

    def scatter_nodes(pos, labels=None, color=None, colorScale='Greens', showScale=False, size=15, opacity=1,
                      bar_title=''):
        # pos is the dict of node positions
        # labels is a list  of labels of len(pos), to be displayed when hovering the mouse over the nodes
        # color is the color for nodes. When it is set as None the Plotly default color is used
        # size is the size of the dots representing the nodes
        # opacity is a value between [0,1] defining the node color opacity

        trace = Scatter3d(x=[],
                          y=[],
                          z=[],
                          mode='markers',
                          marker=Marker(
                              showscale=showScale,
                              # colorscale options
                              # 'Greys' | 'Greens' | 'Bluered' | 'Hot' | 'Picnic' | 'Portland' |
                              # Jet' | 'RdBu' | 'Blackbody' | 'Earth' | 'Electric' | 'YIOrRd' | 'YIGnBu'
                              symbol='circle',
                              colorscale=colorScale,
                              reversescale=True,
                              color=[],
                              size=size,
                              colorbar=dict(
                                  thickness=15,
                                  title=bar_title,
                                  xanchor='left',
                                  titleside='right'
                              ),
                              line=dict(width=2)))

        tempon_x = list(trace['x'])
        tempon_y = list(trace['y'])
        tempon_z = list(trace['z'])
        tempon_marker_color = []

        for nd in nodeID:
            tempon_x.append(pos[nd][0])
            tempon_y.append(pos[nd][1])
            tempon_z.append(pos[nd][2])
            tempon_marker_color.append(color[nd])

        trace['x'] = tuple(tempon_x)
        trace['y'] = tuple(tempon_y)
        trace['z'] = tuple(tempon_z)
        attrib = dict(name='', text=labels, hoverinfo='text', opacity=opacity)  # a dict of Plotly node attributes
        for key, val in attrib.items():
            trace[key] = val
        trace['marker']['color'] = tempon_marker_color
        return trace

    def scatter_edges(G, pos, line_color='#a3a3c2', line_width=1, opacity=.2):
        trace = Scatter3d(x=[],
                          y=[],
                          z=[],
                          mode='lines',
                          )
        for edge in G.edges():
            trace['x'] += tuple([pos[edge[0]][0], pos[edge[1]][0], None])
            trace['y'] += tuple([pos[edge[0]][1], pos[edge[1]][1], None])
            trace['z'] += tuple([pos[edge[0]][2], pos[edge[1]][2], None])
            trace['hoverinfo'] = 'none'
            trace['line']['width'] = line_width
            if line_color is not None:  # when it is None a default Plotly color is used
                trace['line']['color'] = line_color
        return trace

    def make_annotations(pos, text, font_size=14, font_color='rgb(25,25,25)'):
        L = len(pos)
        if len(text) != L:
            raise ValueError('The lists pos and text must have the same len')
        annotations = Annotations()
        for nd in nodeID:
            annotations.append(
                Annotation(
                    text="",
                    x=pos[nd][0], y=pos[nd][1],
                    xref='paper', yref='paper',
                    font=dict(color=font_color, size=font_size),
                    showarrow=False)
            )
        return annotations

    def plot_betweeness_centralities():
        trace1 = scatter_edges(G, pos)
        trace2 = scatter_nodes(pos, color=betweenessCentralScore, showScale=True, labels=labels,
                               bar_title='Betweenness Centrality')
        data = [trace1, trace2]
        layout.title = 'Betweenness Centrality'
        fig = Figure(data=data, layout=layout)
        fig['layout'].update(annotations=make_annotations(pos, labels))
        return plotly.offline.plot({'data': data,
                                    'layout': layout}, include_plotlyjs=False, output_type='div')

    def plot_degrees_centralities():
        trace1 = scatter_edges(G, pos)
        trace2 = scatter_nodes(pos, color=degreeCentralScore, showScale=True, labels=labels,
                               bar_title='Degrees Centrality')
        data = [trace1, trace2]
        layout.title = 'Degrees Centrality'
        fig = Figure(data=data, layout=layout)
        fig['layout'].update(annotations=make_annotations(pos, labels))
        return plotly.offline.plot({'data': data,
                                    'layout': layout}, include_plotlyjs=False, output_type='div')

    def plot_page_rank():
        trace1 = scatter_edges(G, pos)
        trace2 = scatter_nodes(pos, color=pageRankScore, showScale=True, labels=labels, bar_title='PageRank')
        data = [trace1, trace2]
        layout.title = 'PageRank'
        fig = Figure(data=data, layout=layout)
        fig['layout'].update(annotations=make_annotations(pos, labels))
        return plotly.offline.plot({'data': data,
                                    'layout': layout}, include_plotlyjs=False, output_type='div')

    def plot_communites():
        trace1 = scatter_edges(G, pos)
        trace2 = scatter_nodes(pos, color=partition, colorScale='Viridis', labels=labels)
        data = [trace1, trace2]
        layout.title = "Community detection"
        fig = Figure(data=data, layout=layout)
        fig['layout'].update(annotations=make_annotations(pos, labels))
        return plotly.offline.plot({'data': data,
                                    'layout': layout}, include_plotlyjs=False, output_type='div')

    def plot_correlation_heat_map():
        trace = Heatmap(z=np.array(correlations),
                        x=['Betweeness centralities', 'Degrees centralities', 'PageRank'],
                        y=['Betweeness centralities', 'Degrees centralities', 'PageRank'],
                        colorscale='Greens',
                        reversescale=True,
                        zmin=0,
                        zmax=1)
        heatLayout = dict(width=width,
                          height=height,
                          autosize=True,
                          title='Centralities correlation heatmap')
        data = [trace]
        return plotly.offline.plot({'data': data, 'layout': heatLayout}, include_plotlyjs=False, output_type='div')

    plot_betweeness_centralities = plot_betweeness_centralities()
    plot_degrees_centralities = plot_degrees_centralities()
    plot_page_rank = plot_page_rank()
    plot_correlation_heat_map = plot_correlation_heat_map()
    plot_communites = plot_communites()
    return (
        ('Betweeness Centrality', plot_betweeness_centralities), ('Degrees Centrality', plot_degrees_centralities), ('PageRank', plot_page_rank),
        ('Correlation', plot_correlation_heat_map), ('Community', plot_communites))
        #(b_cent_most_important, d_cent_most_important, p_rank_most_important))
