//
//  MainView.swift
//  reco
//
//  Created by 이가영 on 11/13/24.
//

import SwiftUI
import UIKit

struct MainTabView: View {
    @EnvironmentObject var coordinator: CoordinatorImpl
    
    var body: some View {
        ZStack(alignment: .bottomTrailing) {
            TabView {
                let sevendays = getSevenDays()
                HomeView(
                    week: sevendays,
                    selectedItem: sevendays[2]
                )
                .tabItem {
                    Image(systemName: "calendar")
                    Text("스케줄")
                }
                .tag(0)
                
                BView()
                    .tabItem {
                        Color.white
                        Image(systemName: "clock")
                        Text("이력")
                    }
                    .tag(1)
                
                CView()
                    .tabItem {
                        Color.white
                        Image(systemName: "car")
                        Text("차량")
                    }
                    .tag(2)
            }
            .accentColor(.green)
            
            Button {
                coordinator.presentSheet(.check)
            } label: {
                Image(systemName: "plus")
                    .font(.title.weight(.semibold))
                    .padding()
                    .background(Color.green)
                    .foregroundColor(.white)
                    .clipShape(Circle())
                    .shadow(radius: 4, x: 0, y: 4)
            }
            .padding()
            .padding(.bottom, 60)
        }
    }
    
    private func getSevenDays() -> [ScheduleDate] {
        let calendar = Calendar(identifier: .gregorian)
        let fromDate = Calendar.current.date(byAdding: .day, value: -2, to: Date())!
        
        var date = calendar.startOfDay(for: fromDate)
        var model = [ScheduleDate]()
        
        for _ in 1 ... 7 {
            let day = calendar.component(.day, from: date)
            let isToday = calendar.isDateInToday(date)
            let korean = date.dayOfWeekKorean()
            date = calendar.date(byAdding: .day, value: +1, to: date)!
            model.append(ScheduleDate(day: day, isSelected: isToday, formatDay: korean))
        }
        
        return model
    }
}

struct BView: View {
    var body: some View {
        ZStack {
            Text("이력")
        }
    }
}


struct CView: View {
    var body: some View {
        ZStack {
            Text("차량")
        }
    }
}

#Preview {
    MainTabView()
}
