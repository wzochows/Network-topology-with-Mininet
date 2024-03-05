import networkx as nx
import networkx.exception
import json
import requests
import sys

with open('topoData.json', 'r') as json_file:
    data = json.load(json_file)

hostnames = [path["hostname"] for path in data["paths"]]
verge_node = {'first_deviceID': None, 'first_deviceIP': None, 'last_deviceID': None, 'last_deviceIP': None,'ownPort': 1, 'neighbourIP': None, 'neighbourPort': None}
middle_node = {'deviceID': None, 'first_deviceIP': None, 'last_deviceIpIP': None, 'leftPort': None, 'rightPort': None}
weights_on_link = [(path["hostname"], link["switches"], link["bw"], link["delay"]) for path in data["paths"] for link in path["links"]]
existing_links = [['Praga','Hamburg'],['Praga','Belgrad']]

def start_graph():
    """
   The function is used to create a topology map within the application.
    """
    global G
    G = nx.Graph()
    G.add_nodes_from(hostnames)
    for first_node, last_node, bandwidth, delay in weights_on_link:
        bw_weight = (1 / bandwidth) ** 2 * delay ** 0.5
        G.add_edge(first_node, last_node, bw_weight=bw_weight, av_bw=bandwidth, delay=delay)

def find_path(host1, host2, choice):
    """
    This function, utilizing the Dijkstra's algorithm, finds the best route.
    :param host1: the first host involved in the connection (our source)
    :param host2: the second host involved in the connection (our destination)
    :param choice: link weight
    """
    try:
        path = nx.dijkstra_path(G, host1, host2, weight=choice)
    except(networkx.exception.NetworkXNoPath):
        print("The path between" + host1 + "and" + host2 + "is unavailable because there is insufficient available bandwidth.")
    return path

def user_interface():
    """
    This function is responsible for the console interface of the application.
    """
    print("\n Witaj w aplikacji The Best Path!")
    while True:
        action = input(
            "\nChoose the action: \n 1 - Add a new link \n 2 - Display existing links \n 3 - Exit the application \n")
        if action == '1':
            path = user_input()
            start_json("readyLinks")
            taken_data_write_to_json(path)
            end_json("readyLinks")
            send_to_onos('http://192.168.137.138:8181/onos/v1/flows')
            while True:
                want_to_continue = input("Do you want to return to the menu - 1, or exit the application - 2 (enter 1 or 2): ")
                if want_to_continue == '1':
                    break
                elif want_to_continue == '2':
                    sys.exit()
                else:
                    print("You pressed the wrong button. Please choose 1 or 2.")
                    continue
        elif action == '2':
            print(existing_links)
        elif action == '3':
            print("Exiting the application.")
            sys.exit()
        else:
            print("You pressed the wrong button. Please choose a valid action number from the provided options.")

def user_input():
    """
    The function is responsible for retrieving connection details from the user.
    :return: optimal path
    """
    print(hostnames)
    flag1 = False
    flag2 = False
    while not flag1 and not flag2: 
        host1 = input("Select the first city from the list for the connection: ")
        if host1 not in hostnames:
            print("The city you entered is not on the list. Please choose a valid city.")
            continue
        else:
            flag1 =True
        host2 = input("Wybierz z listy drugie do połączenia: ")
        if host2 not in hostnames:
            print("The city you entered is not on the list. Please select a correct city.")
            continue
        else:
            flag2 =True
        if host2 == host1:
            print("The same city was provided. Please choose a different city.")
            flag1 = False
            flag2 = False
            continue
        if len(existing_links) > 0:
            for link in existing_links:
                if host1 == link[0] and host2 == link[-1] or host1 == link[-1] and host2 == link[0]:
                    print("The provided connection already exists. Please choose a different connection.")
                    flag1 = False
                    flag2 = False

    while True:
        preference = input(
            "What is the priority for this connection?\n1 - Best throughput \n2 - Minimum latency: \n")
        if preference == "1":
            choice = 'bw_weight'
            break
        if preference == "2":
            choice = 'delay'
            break
        else:
            print("Choose the correct number")
            continue
    while True:
        try:
            requested_bw = int(input("What throughput do you expect? [Mbps]"))
        except ValueError:
            print("Please enter the number.")
            continue

        path = find_path(host1, host2, choice)
        for i in range(len(path) - 1):
            av_bw = G.edges[path[i], path[i + 1]]['av_bw']
            if i == 0:
                max_bw = av_bw
            elif av_bw < max_bw:
                max_bw = av_bw
        if requested_bw > max_bw:
            print("The requested throughput is too large. \nPlease provide a smaller value than " + str(max_bw) + '.')
            continue
        else:
            existing_links.append(path)
            print("The following path has been assigned: " + str(path))
            print("Received throughput: " + str(requested_bw) + ' Mbps')
            reduce_available_bw(path, requested_bw)
            return path

def start_json(filename):
    """
    The function begins a JSON file.
    :param filename: name of the file
    """
    with open(str(filename) + ".json", "w") as f:
        f.write("{ \n \"flows\": [\n")

def fill_the_template(ID, IP, port):
    """
    The function replaces appropriate data according to the template pattern.
    :param ID: Device ID of the source host
    :param IP: IPv4 of the destination host
    :param port: Port through which the link is directed
    :return: Filled template
    """
    with open('template.json', 'r') as json_file:
        template_content = json_file.read()
    data = json.loads(template_content)
    data["deviceId"] = ID
    data["treatment"]["instructions"][0]["port"] = port
    IP = IP + "/32"
    data["selector"]["criteria"][1]["ip"] = IP
    return data

def write_to_json(klamerki, filename):
    """
    The function writes filled templates to a JSON file.
    :param curly_brackets: filled template
    :param filename: JSON file
    """
    with open(str(filename) + ".json", "a") as f:
        f.write(json.dumps(klamerki, indent=5))
        f.write(', \n')

def end_json(filename):
    """
    The function appropriately closes the JSON file.
    :param filename: name of the file
    """
    with open(str(filename) + '.json', "a") as f:
        size = f.tell()
        f.seek(size - 4)
        f.truncate(size - 4)
        f.write("\n ] \n }")

def taken_data_write_to_json(received_list):
    """
    The function saves data to a JSON file.
    :param received_list: list returned from the algorithm
    """
    first_device_ID, first_device_IP = next(((path["deviceId"], path["IPv4"]) for path in data["paths"] if received_list[0] == path["hostname"]),(None, None))
    last_device_ID, last_device_IP = next(((path["deviceId"], path["IPv4"]) for path in data["paths"] if received_list[len(received_list) - 1] == path["hostname"]), (None, None))

    for switch in range(len(received_list)):
        if switch == 0:  # no left neighbor = first node
            for path in data["paths"]:
                if received_list[switch] == path["hostname"]:
                    for link in path["links"]:
                        if link["switches"] == received_list[switch + 1]:
                            first_node_right_port = link["output"]
            verge_node.update({'first_deviceID': first_device_ID, 'first_deviceIP': first_device_IP, 'last_deviceID': last_device_ID,'last_deviceIP': last_device_IP, 'neighbourPort': first_node_right_port})
            
            write_to_json(fill_the_template(verge_node["first_deviceID"], verge_node["first_deviceIP"], verge_node["ownPort"]),"readyLinks")  # s1-h1
            write_to_json(fill_the_template(verge_node["first_deviceID"], verge_node["last_deviceIP"], verge_node["neighbourPort"]), "readyLinks")  # s1-last_node

        elif switch + 2 > len(received_list):  #no right neighbor = last node
            for path in data["paths"]:
                if received_list[switch] == path["hostname"]:
                    for link in path["links"]:
                        if link["switches"] == received_list[switch - 1]:
                            last_node_left_port = link["output"]
            verge_node.update({'first_deviceID': first_device_ID, 'first_deviceIP': first_device_IP, 'last_deviceID': last_device_ID,'last_deviceIP': last_device_IP, 'neighbourPort': last_node_left_port})
            
            write_to_json(fill_the_template(verge_node["last_deviceID"], verge_node["last_deviceIP"], verge_node["ownPort"]),"readyLinks")  # last_node-last_node)
            write_to_json(fill_the_template(verge_node["last_deviceID"], verge_node["first_deviceIP"],verge_node["neighbourPort"]), "readyLinks")  # last_node - first_node

        else:  #has both neighbors = middle node
            device_id = next((path["deviceId"] for path in data["paths"] if received_list[switch] == path["hostname"]),None)
            for path in data["paths"]:
                if received_list[switch] == path["hostname"]:
                    for link in path["links"]:
                        if link["switches"] == received_list[switch - 1]:
                            leftport = link["output"]
                        if link["switches"] == received_list[switch + 1]:
                            rightport = link["output"]
            middle_node.update({'deviceID': device_id, 'first_deviceIP': first_device_IP, 'leftPort': leftport,'last_deviceIP': last_device_IP, 'rightPort': rightport})
            
            write_to_json(fill_the_template(middle_node["deviceID"], middle_node["first_deviceIP"], middle_node["leftPort"]),"readyLinks")  # current_node - first_node
            write_to_json(fill_the_template(middle_node["deviceID"], middle_node["last_deviceIP"], middle_node["rightPort"]),"readyLinks")  # current_node - last_node

def send_to_onos(path):
    """
    The function sends data to the ONOS controller for configuring links.
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    with open('readyLinks.json', 'r+') as f:
        data = f.read()
        response = requests.post(path, headers=headers, data=data,
                                 auth=('karaf', 'karaf'))
        print("Response from the ONOS service.\n" + str(response))
        print(response.status_code)
        f.truncate(0)

def reduce_available_bw(path: list, bw):
    """
    The function updates the available bandwidth.
    :param path: current path
    :param bw: bandwidth to be decreased (requested)
    """
    for i in range(len(path) - 1):
        G.edges[path[i], path[i + 1]]['av_bw'] -= bw
        if G.edges[path[i], path[i + 1]]['av_bw'] == 0:
            G.remove_edge(path[i], path[i + 1])
            continue
        G.edges[path[i], path[i + 1]]['bw_weight'] = (G.edges[path[i], path[i + 1]]['delay'] ** 0.5 /G.edges[path[i], path[i + 1]]['av_bw']) ** 2

if __name__ == "__main__":
    start_graph()
    user_interface()









