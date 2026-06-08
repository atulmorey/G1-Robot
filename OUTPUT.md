john@john-Precision-7530:~/G1-Robot$ sed -n '80,200p' ~/ros2_ws/src/unitree_ros2/example/src/src/g1/high_level/loco_client_example.cpp
      if (arg_pair.first == "get_swing_height") {
        float swing_height = NAN;
        auto ret = client_.GetSwingHeight(swing_height);
        if (!handleActionError(ret)) {
          RCLCPP_ERROR(this->get_logger(), "GetSwingHeight failed");
          continue;
        }
        RCLCPP_INFO(this->get_logger(), "current swing_height: %f",
                    swing_height);
      }

      if (arg_pair.first == "get_stand_height") {
        float stand_height = NAN;
        auto ret = client_.GetStandHeight(stand_height);
        if (!handleActionError(ret)) {
          RCLCPP_ERROR(this->get_logger(), "GetStandHeight failed");
          continue;
        }
        RCLCPP_INFO(this->get_logger(), "current stand_height: %f",
                    stand_height);
      }

      if (arg_pair.first == "get_phase") {
        std::vector<float> phase;
        auto ret = client_.GetPhase(phase);
        if (!handleActionError(ret)) {
          RCLCPP_ERROR(this->get_logger(), "GetPhase failed");
          continue;
        }
        std::stringstream ss;
        ss << "current phase: (";
        for (const auto &p : phase) {
          ss << p << ", ";
        }
        ss << ")";
        RCLCPP_INFO(this->get_logger(), "%s", ss.str().c_str());
      }

      if (arg_pair.first == "set_fsm_id") {
        int fsm_id = std::stoi(arg_pair.second);
        auto ret = client_.SetFsmId(fsm_id);
        if (!handleActionError(ret)) {
          RCLCPP_ERROR(this->get_logger(), "SetFsmId failed");
          continue;
        }
        RCLCPP_INFO(this->get_logger(), "set fsm_id to %d", fsm_id);
      }

      if (arg_pair.first == "set_balance_mode") {
        int balance_mode = std::stoi(arg_pair.second);
        auto ret = client_.SetBalanceMode(balance_mode);
        if (!handleActionError(ret)) {
          RCLCPP_ERROR(this->get_logger(), "SetBalanceMode failed");
          continue;
        }
        RCLCPP_INFO(this->get_logger(), "set balance_mode to %d", balance_mode);
      }

      if (arg_pair.first == "set_swing_height") {
        float swing_height = std::stof(arg_pair.second);
        auto ret = client_.SetSwingHeight(swing_height);
        if (!handleActionError(ret)) {
          RCLCPP_ERROR(this->get_logger(), "SetSwingHeight failed");
          continue;
        }
        RCLCPP_INFO(this->get_logger(), "set swing_height to %f", swing_height);
      }

      if (arg_pair.first == "set_stand_height") {
        float stand_height = std::stof(arg_pair.second);
        auto ret = client_.SetStandHeight(stand_height);
        if (!handleActionError(ret)) {
          RCLCPP_ERROR(this->get_logger(), "SetStandHeight failed");
          continue;
        }
        RCLCPP_INFO(this->get_logger(), "set stand_height to %f", stand_height);
      }

      if (arg_pair.first == "set_velocity") {
        std::vector<float> param = stringToFloatVector(arg_pair.second);
        auto param_size = param.size();
        float vx = NAN;
        float vy = NAN;
        float omega = NAN;
        float duration = NAN;
        if (param_size == 3) {
          vx = param.at(0);
          vy = param.at(1);
          omega = param.at(2);
          duration = 1.F;
        } else if (param_size == 4) {
          vx = param.at(0);
          vy = param.at(1);
          omega = param.at(2);
          duration = param.at(3);
        } else {
          RCLCPP_ERROR(this->get_logger(),
                       "Invalid param size for method SetVelocity: %zu",
                       param_size);
          continue;
        }

        auto ret = client_.SetVelocity(vx, vy, omega, duration);
        if (!handleActionError(ret)) {
          RCLCPP_ERROR(this->get_logger(), "SetVelocity failed");
          continue;
        }
        RCLCPP_INFO(this->get_logger(), "set velocity to %s",
                    arg_pair.second.c_str());
      }

      if (arg_pair.first == "damp") {
        auto ret = client_.Damp();
        if (!handleActionError(ret)) {
          RCLCPP_ERROR(this->get_logger(), "Damp failed");
          continue;
        }
        RCLCPP_INFO(this->get_logger(), "Damp command sent");
      }

      if (arg_pair.first == "start") {
john@john-Precision-7530:~/G1-Robot$ 
