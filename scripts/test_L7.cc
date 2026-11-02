/*
 * Benchmark L7: FindFlow() is O(n)
 * 
 * Crea un Ipv4FlowClassifier, lo puebla con N flujos sintéticos
 * usando UdpHeader válidos, y mide el tiempo de N llamadas a FindFlow().
 * 
 * Usa #pragma GCC optimize("O0") y un puntero a función para evitar
 * que el compilador optimice las llamadas.
 */
#pragma GCC optimize("O0")

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/udp-header.h"
#include <chrono>
#include <vector>
#include <iostream>
#include <memory>

using namespace ns3;

// Puntero a función para FindFlow()
typedef Ipv4FlowClassifier::FiveTuple (Ipv4FlowClassifier::*FindFlowPtr)(FlowId) const;

int main(int argc, char *argv[])
{
    std::vector<uint32_t> sizes = {100, 500, 1000, 5000, 10000, 25000, 50000};
    int repetitions = 5;

    FindFlowPtr findFlowPtr = &Ipv4FlowClassifier::FindFlow;

    std::cout << "N flows,Time total (us),Time per call (us)" << std::endl;

    for (uint32_t N : sizes)
    {
        double total_time_us = 0;
        for (int rep = 0; rep < repetitions; rep++)
        {
            auto classifier = std::make_shared<Ipv4FlowClassifier>();

            // Poblar el classifier con N flujos sintéticos
            std::vector<FlowId> flow_ids;
            for (uint32_t i = 0; i < N; i++)
            {
                Ipv4Header ipHeader;
                ipHeader.SetSource(Ipv4Address("10.1.1.1"));
                ipHeader.SetDestination(Ipv4Address("10.1.1.2"));
                ipHeader.SetProtocol(17); // UDP

                // Crear un packet con un header UDP válido
                Ptr<Packet> packet = Create<Packet>();
                UdpHeader udpHeader;
                udpHeader.SetSourcePort(10000 + i);
                udpHeader.SetDestinationPort(9000);
                packet->AddHeader(udpHeader);

                uint32_t flowId, packetId;
                classifier->Classify(ipHeader, packet, &flowId, &packetId);
                flow_ids.push_back(flowId);
            }

            // Medir N llamadas a FindFlow()
            volatile uint64_t sink = 0;
            auto start = std::chrono::high_resolution_clock::now();
            for (FlowId fid : flow_ids)
            {
                Ipv4FlowClassifier::FiveTuple tuple = (classifier.get()->*findFlowPtr)(fid);
                sink += tuple.sourcePort;
                asm volatile("" ::: "memory");
            }
            auto end = std::chrono::high_resolution_clock::now();

            std::chrono::duration<double, std::micro> elapsed = end - start;
            total_time_us += elapsed.count();
            if (sink == 0xFFFFFFFF) { std::cout << "impossible" << std::endl; }
        }

        double avg_total_us = total_time_us / repetitions;
        double avg_per_call_us = avg_total_us / N;
        std::cout << N << "," << avg_total_us << "," << avg_per_call_us << std::endl;
    }

    return 0;
}
