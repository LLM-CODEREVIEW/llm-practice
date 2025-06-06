//
//  MainView.swift
//  reco
//
//  Created by 이가영 on 11/17/24.
//

import SwiftUI

struct ScheduleDate: Identifiable, Equatable {
    var id: UUID = UUID()
    let day: Int
    var isSelected: Bool
    let formatDay: String
    
    static func == (lhs: ScheduleDate, rhs: ScheduleDate) -> Bool {
        lhs.day == rhs.day && lhs.formatDay == rhs.formatDay
    }
}

// 위치 정보를 담을 모델
struct Location: Identifiable {
    let id = UUID()
    let name: String
    let address: String
}

struct Task {
    let date: Int
    let depart: Location
    let destination: Location
    let waypoints: [Location]
}

struct HomeView: View {
    @State var week: [ScheduleDate]
    @State var selectedItem: ScheduleDate
    @State var task: Task = .init(
        date: Calendar(identifier: .gregorian).component(.day, from: Date()),
        depart: Location(
            name: "서울역",
            address: "서울특별시 용산구 한강대로 405"
        ),
        destination: Location(
            name: "서울역",
            address: "서울특별시 용산구 한강대로 405"
        ),
        waypoints:  [
            Location(name: "대전역", address: "대전광역시 동구 중앙로 215"),
            Location(name: "동대구역", address: "대구광역시 동구 동대구로 550"),
            Location(name: "울산역", address: "울산광역시 울주군 삼남면 울산역로 177")
        ]
    )
    
    @State private var isWaypointsExpanded = true
    
    var body: some View {
        VStack(alignment: .leading) {
            Text("1020님의 스케줄")
                .font(.title)
                .bold()
                .padding(.horizontal, 20)
                .padding(.bottom, 20)
            Text("2024년 11월")
                .font(.headline)
                .foregroundColor(.gray)
                .padding(.horizontal, 20)
            ScrollView(.horizontal, showsIndicators: false) {
                HStack {
                    ForEach(week, id: \.id) { day in
                        ItemView(item: day, isSelected: self.selectedItem == day)
                            .onTapGesture {
                                self.selectedItem = day
                            }
                    }
                }
                .padding(.horizontal, 20)
            }
            .frame(height: 80)
            Text("Task")
                .font(.headline)
                .foregroundColor(.gray)
                .padding()
            let locationList = List {
                Section("출발지") {
                    LocationRow(location: task.depart)
                }
                
                // 경유지 섹션 (확장/축소 가능)
                Section("경유지") {
                    DisclosureGroup(
                        isExpanded: $isWaypointsExpanded,
                        content: {
                            ForEach(task.waypoints) { waypoint in
                                LocationRow(location: waypoint)
                            }
                        },
                        label: {
                            Text("경유지 총 \(task.waypoints.count)개")
                                .font(.headline)
                        }
                    )
                }
                
                // 도착지 섹션
                Section(header: Text("도착지")) {
                    LocationRow(location: task.destination)
                }
            }
            .listStyle(.insetGrouped)
            
            if selectedItem.day == task.date {
                locationList
            } else {
                Rectangle()
                    .background(.gray).opacity(0.1)
                    .ignoresSafeArea()
                    .overlay {
                        Text("일정이 없습니다.")
                            .multilineTextAlignment(.center)
                            .font(.title)
                            .bold()
                    }
            }
        }

    }
    
    struct ItemView: View {
        let item: ScheduleDate
        let isSelected: Bool
        
        var body: some View {
            VStack(spacing: 10) {
                Text("\(item.day)")
                    .foregroundStyle(.black)
                    .font(.headline)
                Text("\(item.formatDay)")
                    .foregroundStyle(.black)
                    .font(.headline)
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 12)
            .background(
                RoundedRectangle(cornerRadius: 10)
                    .fill(isSelected ? Color.green : Color.gray.opacity(0.3))
                    .opacity(0.5)
            )
            .shadow(color: .black.opacity(0.1), radius: 4, x: 6, y: 0)
            .foregroundColor(isSelected ? .white : .black)
            .animation(.easeInOut, value: isSelected)
        }
    }
    
}

struct LocationRow: View {
    let location: Location
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(location.name)
                .font(.headline)
            Text(location.address)
                .font(.subheadline)
                .foregroundColor(.gray)
        }
        .padding(.vertical, 4)
    }
}

